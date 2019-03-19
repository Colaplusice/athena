#!/usr/bin/env bash

function run() {
   gunicorn -b  0.0.0.0:5000 --access-logfile - --error-logfile - run:app

}

function deploy() {
   ssh  ubuntu@111.231.82.45 "cd /home/ubuntu/flask_project/athena; git pull"
   ssh  ubuntu@111.231.82.45 "cd /home/ubuntu/flask_project/athena; /home/ubuntu/miniconda3/bin/docker-compose up -d --build"
   ssh  ubuntu@111.231.82.45 "cd /home/ubuntu/flask_project/athena; git push github master"
   ssh icecola@206.189.81.45 "cd /home/icecola/flask_project/athena; git pull"
   ssh icecola@206.189.81.45 "cd /home/icecola/flask_project/athena; /home/icecola/miniconda/bin/docker-compose up -d --build"
}
function run_celery() {
    celery worker -B -A run_celery.celery -l info
}
function run_celery_beat() {
    celery beat -A run_celery.celery  -l info
}

function migrate() {
flask user create_user
}
function create_db() {
   mysql -u root -pnewpass -e "create database $1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
}
Action=$1
shift
 case "$Action" in
 run)
    run ;;
 deploy)
    deploy;;
 run_celery)
 run_celery;;
 run_celery_beat)
 run_celery_beat;;
 migrate)
 migrate;;
 create_db )
 create_db "$1";;
    *) echo 'usage: ./boot.sh command
     command:
     runserver:                  run
     update code and deploy:     deploy
     run celery worker           run_celery
     run celery beat             run_celery_beat
     migrate data                migrate
     create_db                   create_db [dbname]
     ' ;;

esac
