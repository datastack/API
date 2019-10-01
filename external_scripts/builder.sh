#!/bin/bash

GIT_URL="https://github.com/datastack/API.git"
DOCKER_ENV_FILE=/root/.env

if [ -d "./API" ]; then
  echo "Removing API directory"
  rm -rf ./API
fi

git clone -b master $GIT_URL
docker rm -v -f lsapi
docker build -t lsapi:onbuild -f ./API/Dockerfile_onbuild ./API
docker build -t lsapi:latest -f ./API/Dockerfile ./API
docker run -d -p 8000:8000 --env-file $DOCKER_ENV_FILE --name lsapi --restart-always lsapi:latest