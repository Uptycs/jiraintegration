#!/bin/bash

docker stop jira_container && docker rm jira_container && docker rmi uptycsjira:1.0
docker build  --force-rm --tag uptycsjira:1.0 $PWD
docker run -d --name jira_container -p 8080:8080 -e LISTEN_PORT='8080'uptycsjira:1.0
docker logs -f jira_container

