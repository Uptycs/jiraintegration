#!/usr/bin/env python

###############################################################################
# import python libraries
###############################################################################
import os
import configparser
import json
import base64
from jira import JIRA
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
###############################################################################
# load config.ini 
###############################################################################
config_ini = configparser.ConfigParser()
config_ini.read(os.environ.get('CONFIG_FILE'))
service_port =  config_ini['SERVICE']['port']
token_expiration = config_ini['SERVICE']['token_expiration']
master_user = config_ini['SERVICE']['username']
master_password = config_ini['SERVICE']['password']
debug = config_ini['SERVICE']['debug']

###############################################################################
# jira server information
###############################################################################
jira_url = config_ini['JIRA']['url']
jira_user = config_ini['JIRA']['username']
jira_passwrd = config_ini['JIRA']['token']
jira_project = config_ini['JIRA']['project_key']
jira_issue_type = config_ini['JIRA']['issuetype']
jira_search_string = config_ini['JIRA']['search_string']

jira_summary_prefix = config_ini['CREATE_JIRA']['summary_prefix']

jira_summary_keys = config_ini['CREATE_JIRA']['summary_keys']
jira_key_seprator = config_ini['CREATE_JIRA']['key_seprator']
orig_jira_summary_key_array = jira_summary_keys.split(jira_key_seprator)
jira_summary_key_array = []
for sum_key in orig_jira_summary_key_array:
    jira_summary_key_array.append(sum_key.strip())
    

###############################################################################
# jira connection
###############################################################################

jira= JIRA(basic_auth=(jira_user, jira_passwrd), 
           options={'server': jira_url})
 

###############################################################################
# Flask app variable and config
###############################################################################
app = Flask(__name__)
app.config['SECRET_KEY'] = 'GlcKU+F5gACsgjoVqUtXkdl6tVIgDErYpXNjDeBWQg4='
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['MASTER_USERNAME'] = master_user
app.config['MASTER_PASSWORD'] = master_password
app.config['PORT'] = service_port


###############################################################################
# extensionsa 
###############################################################################
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/alert', methods=['POST'])
@auth.login_required
def alert():

    # get the raw alert data 
    alert_data = request.get_data(as_text=True).replace('\\n','\n')
    alert_data = alert_data.replace(': "{', ': {')
    alert_data = alert_data.replace('}"\n', '}\n') 
    
    alert_json = json.loads(alert_data)
    if debug:
        print("DEBUG: alert_json: %s" % (json.dumps(alert_json)))
    
    jira_summary = jira_summary_prefix

    for sum_key in jira_summary_key_array:
        if alert_json.get(sum_key):
            jira_summary = "%s : %s" % (jira_summary, 
                                      alert_json.get(sum_key))
    jira_description = ""

    for key, value in alert_json.items():
            if key == 'Metadata':
                new_value = json.dumps(value, ensure_ascii=True)
                jira_description =  "%s%s: %s\n" % (jira_description,
                                                    key,
                                                    new_value)
            else:
                jira_description =  "%s%s: %s\n" % (jira_description,
                                                    key,
                                                    value)
    if debug:
        print("DEBUG: Summary: %s" %  (jira_summary))
        print("DEBUG: Description: %s" % (jira_description))

    search_string = ("%s AND summary ~ \"%s\"" % 
                    (jira_search_string, jira_summary))
    query = None
    new_issue = None

    if debug:
        print("DEBUG: search string: %s" % (search_string))

    query = jira.search_issues(jql_str=search_string)
    if query:
        jira.add_comment(query[0], jira_description) 
        return jsonify({'issue': str(query[0]),
                        'project': jira_project,
                        'summary': jira_summary,
                        'description': jira_description,
                        'issuetype': jira_issue_type})
    else:
        new_issue =  jira.create_issue(project=jira_project,
                                summary=jira_summary, 
                                description=jira_description,
                                issuetype={'name': jira_issue_type}) 
        return jsonify({'issue': new_issue.key,
                        'project': jira_project,
                        'summary': jira_summary,
                        'description': jira_description,
                        'issuetype': {'name': jira_issue_type}})
    return jsonify({'error': 'non able to create/update jira'})

@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(int(token_expiration)*3600)
    return jsonify({'token': token.decode('ascii'), 
                    'duration': token_expiration })


@app.route('/api/BasicAuthToken')
@auth.login_required
def get_basic_auth_token():
    user_string = "%s:%s" % (master_user, master_password)
    token = base64.b64encode(user_string.encode())
    return_token = "Basic %s" % (str(token, "utf-8"))
    return jsonify({'authorization': return_token})


if not os.path.exists('db.sqlite'):
    db.create_all()
username = master_user
password = master_password

if username is None or password is None:
    abort(400)
user = User(username=username)
user.hash_password(password)
db.session.add(user)
db.session.commit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=int(service_port))
