#!/bin/bash

docker build -t 'nginx_balance_image' .
docker run -itd --name nginx_balance -h nginx_balance -p 1700:1700 nginx_balance_image