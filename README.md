Uptycs Jira Integration
=======================

This repository contains the Dockerfile and other code which user can use to build a container for transforming Uptycs alert to Jira Ticket.<br>

For running the the container in secure mode, user can copy the necessary certificate in `app/ssl/` directory and can update `app/nginx.conf` file `ssl` and `ssl_*` parameters.<br>

For creating a ticket in jira, a user need to pass following information in `app/config/config.ini` file.<br>

```
[SERVICE]
; container service username
username = serviceuser

; container service password
password = servicepassword

; container service password
port = 8080

; token expiration in hours
token_expiration = 24

; run container in debug mode
debug = True

[JIRA]

url = https://<url>

; jira username
username = jira_user

; jira token
token = jira_token

; jira project key
project_key = PRJ123

; jira issue type
issuetype = Task

; jira search string
search_string = project=PRJ123 AND status not in (Done, "Won't fix", "Not a bug")

[CREATE_JIRA]
; Uptycs alerts give following fields:
; 1. Alert ID
; 2. Code
; 3. Severity
; 4. Description
; 5. Key
; 6. Value
; 7. Asset ID
; 8. Host name
; 9. Metadata

; In jira summary string user wants to add
summary_prefix = Uptycs Alerts: 

; key seprator of fields user want to use for listing summary keys
key_seprator = , 

; Uptycs alert fields for jira summary string 
summary_keys = Severity,Description

```

Building a container
--------------------

After cloning the repo use following command build a container:

    $ cd     $ docker build  --force-rm --tag uptycsjira:1.0 $PWD
    $ docker build  --force-rm --tag uptycsjira:1.0 $PWD
    $ docker run -d --name uptycs_jira -p 8080:8080 -e LISTEN_PORT='8080'uptycsjira:1.0

Note: a user can modify the port number as mentioned above.

If you want to view contiainer log, you can use following command:

    $ docker logs -f uptycs_jira



API Documentation
-----------------

 Container supports following API for integration:

- POST **/api/alert**

    Post the alerts to container. Based on configuration alert will be sent to Jira for new/update task/ticket.<br>
    The body must contain a JSON object that defines `username` and `password` fields or basic authorization.<br>
    On success a status code 201 is returned. The body of the response contains a JSON object with the alert JSON.<br>
    On failure status code 400 (bad request) is returned.<br>
    Notes:
    - The password is hashed before it is stored in the database. Once hashed, the original password is discarded.
    - In a production deployment secure HTTP must be used to protect the password in transit.

- GET **/api/token**

    Return an authentication token.<br>
    This request must be authenticated using a HTTP Basic Authentication header.<br>
    On success a JSON object is returned with a field `token` set to the authentication token for the user and a field `duration` set to the (approximate) number of hours the token is valid.<br>
    On failure status code 401 (unauthorized) is returned.

- GET **/api/BasicAuthToken**

    Return a Basic Authorization code.<br>
    This request must be authenticated using a HTTP Basic Authentication header. Instead of username and password, the client can provide a valid authentication token in the username field. If using an authentication token the password field is not used and can be set to any value.<br>
    On success a JSON object with data for the authenticated user is returned.<br>
    On failure status code 401 (unauthorized) is returned.

Example
-------

The following `curl` command a new alert in JIRA with username `serviceuser` and password `servicepassword`:

    $ curl -u serviceuser:servicepassword -i -X POST -H "Content-Type: application/json" -d '{\n"Alert ID": "a328dc3e-efa7-4267-9be4-6ba4e9c196aa",\n"Code": "CRITICAL_FILE",\n"Severity": "high",\n"Description": "File event",\n"Key": "path",\n"Value": "/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw",\n"Asset ID": "3cc4d442-e188-509b-af03-d492810dd13a",\n"Host name": "vibhors-macbook.fios-router.home",\n"Metadata" : {"action":"ATTRIBUTES_MODIFIED","category":"2a282be3-6afa-4bc4-b397-fdaf26fd77ec","path":"/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw"}\n}' http://127.0.0.1:8080/api/alert

    HTTP/1.1 200 OK
    Server: nginx/1.15.8
    Date: Wed, 01 May 2019 23:15:57 GMT
    Content-Type: application/json
    Content-Length: 607
    Connection: keep-alive
    {"alert_json":{"Alert ID":"a328dc3e-efa7-4267-9be4-6ba4e9c196aa","Asset ID":"3cc4d442-e188-509b-af03-d492810dd13a","Code":"CRITICAL_FILE","Description":"File event","Host name":"vibhors-macbook.fios-router.home","Key":"path","Metadata":{"action":"ATTRIBUTES_MODIFIED","category":"2a282be3-6afa-4bc4-b397-fdaf26fd77ec","path":"/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw"},"Severity":"high","Value":"/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw"},"issue":"UI123-23","issuetype":"Task","project":"UI123","summary":"Uptycs Alerts: : high : File event"}


To avoid sending username and password with every request an authentication token can be requested:

    $ curl -u serviceuser:servicepassword -i -X GET http://127.0.0.1:8080/api/token
    HTTP/1.1 200 OK
    Server: nginx/1.15.8
    Date: Wed, 01 May 2019 23:19:02 GMT
    Content-Type: application/json
    Content-Length: 194
    Connection: keep-alive
          {"duration":"24","token":"eyJhbGciOiJIUzI1NiIsImV4cCI6MTM4NTY2OTY1NSwiaWF0IjoxMzg1NjY5MDU1fQ.eyJpZCI6MX0.XbOEFJkhjHJ5uRINh2JA1BPzXjSohKYDRT472wGOvjc"}


And now during the token validity period there is no need to send username and password to authenticate anymore:

    $ curl -u eyJhbGciOiJIUzI1NiIsImV4cCI6MTM4NTY2OTY1NSwiaWF0IjoxMzg1NjY5MDU1fQ.eyJpZCI6MX0.XbOEFJkhjHJ5uRINh2JA1BPzXjSohKYDRT472wGOvjc:x -i -X POST -H "Content-Type: application/json" -d '{\n"Alert ID": "a328dc3e-efa7-4267-9be4-6ba4e9c196aa",\n"Code": "CRITICAL_FILE",\n"Severity": "high",\n"Description": "File event",\n"Key": "path",\n"Value": "/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw",\n"Asset ID": "3cc4d442-e188-509b-af03-d492810dd13a",\n"Host name": "vibhors-macbook.fios-router.home",\n"Metadata" : {"action":"ATTRIBUTES_MODIFIED","category":"2a282be3-6afa-4bc4-b397-fdaf26fd77ec","path":"/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw"}\n}' http://127.0.0.1:8080/api/alert

    HTTP/1.1 200 OK
    Server: nginx/1.15.8
    Date: Wed, 01 May 2019 23:15:57 GMT
    Content-Type: application/json
    Content-Length: 607
    Connection: keep-alive
    {"alert_json":{"Alert ID":"a328dc3e-efa7-4267-9be4-6ba4e9c196aa","Asset ID":"3cc4d442-e188-509b-af03-d492810dd13a","Code":"CRITICAL_FILE","Description":"File event","Host name":"vibhors-macbook.fios-router.home","Key":"path","Metadata":{"action":"ATTRIBUTES_MODIFIED","category":"2a282be3-6afa-4bc4-b397-fdaf26fd77ec","path":"/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw"},"Severity":"high","Value":"/Users/vibhorkumar/Downloads/works/work_scrathpad.txt.sb-d430f1a0-akA9Iw"},"issue":"UI123-23","issuetype":"Task","project":"UI123","summary":"Uptycs Alerts: : high : File event"}

Once the token expires it cannot be used anymore and the client needs to request a new one. Note that in this last example the password is arbitrarily set to `x`, since the password isn't used for token authentication.

An interesting side effect of this implementation is that it is possible to use an unexpired token as authentication to request a new token that extends the expiration time. This effectively allows the client to change from one token to the next and never need to send username and password after the initial token was obtained.

If user wants to use Authorization key in header, then base authentication can be generated using following API:

    $ curl -u eyJhbGciOiJIUzI1NiIsImV4cCI6MTM4NTY2OTY1NSwiaWF0IjoxMzg1NjY5MDU1fQ.eyJpZCI6MX0.XbOEFJkhjHJ5uRINh2JA1BPzXjSohKYDRT472wGOvjc:x -i -X GET http://127.0.0.1:8080/api/BasicAuthToken

    HTTP/1.1 200 OK
    Server: nginx/1.15.8
    Date: Wed, 01 May 2019 23:24:49 GMT
    Content-Type: application/json
    Content-Length: 95
    Connection: keep-alive
    {"authorization":"Basic dmt1bWFyOlZydjZNaDhGYU1xTlA5dVArekhmRWFHU24wSzJ3YTNKZmJBRVhMQWdoVkU9"}
