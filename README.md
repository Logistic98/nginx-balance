## 使用Nginx配置服务的负载均衡

需求情景：一台服务器上有多张显卡，用不同的显卡部署了多个大模型服务，现在想要提高大模型服务的并发量，可以使用Nginx负载均衡来实现。

### 1. Nginx负载均衡的示例

假设有3个服务，分别是1701、1702、1703端口，现在想要将其使用Nginx进行负载均衡，统一用1700端口来访问。

```
.
├── Dockerfile
├── nginx.conf
├── nginx_balance.conf
├── proxy.conf
└── build.sh
```

Dockerfile

```Dockerfile
# 设置基础镜像
FROM nginx

# 放置nginx配置
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx_balance.conf /etc/nginx/conf.d/nginx_balance.conf
COPY proxy.conf /etc/nginx
```

nginx.conf

```ini
user  root;
worker_processes  auto;

error_log  /var/log/nginx/error.log notice;
pid        /var/run/nginx.pid;


events {
    worker_connections  1024;
}


http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

    include /etc/nginx/conf.d/*.conf;
}
```

nginx_balance.conf

```ini
upstream nginx_balance {
        server xxx.xxx.xxx.xxx:1701 weight=1;
        server xxx.xxx.xxx.xxx:1702 weight=2;
        server xxx.xxx.xxx.xxx:1703 weight=3;
}
server {
    listen       1700;
    server_name  127.0.0.1;
    location ~* ^(/) {
        gzip on;
        gzip_vary on;
	      gzip_min_length 1k;
	      gzip_buffers 16 16k;
        gzip_http_version 1.1;
        gzip_comp_level 9;
        gzip_types text/plain application/javascript application/x-javascript text/css text/xml text/javascript application/json;
        proxy_pass http://nginx_balance;
        client_max_body_size    48m;
        include proxy.conf;
    }
}
```

proxy.conf

```ini
proxy_connect_timeout 900s;
proxy_send_timeout 900;
proxy_read_timeout 900;
proxy_buffer_size 32k;
proxy_buffers 4 64k;
proxy_busy_buffers_size 128k;
proxy_redirect off;
proxy_hide_header Vary;
proxy_set_header Accept-Encoding '';
proxy_set_header Referer $http_referer;
proxy_set_header Cookie $http_cookie;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

build.sh

```shell
#!/bin/bash

docker build -t 'nginx_balance_image' .
docker run -itd --name nginx_balance -h nginx_balance -p 1700:1700 nginx_balance_image
```

上传到服务器上之后，给 build.sh 添加可执行权限，执行该脚本即可。

### 2. Nginx负载均衡的方式

**[1] 轮询**

轮询方式是Nginx负载默认的方式，所有请求都按照时间顺序分配到不同的服务上，如果服务挂掉了，可以自动剔除。

```ini
upstream  nginx_balance {
        server xxx.xxx.xxx.xxx:1701;
        server xxx.xxx.xxx.xxx:1702;
}
```

**[2] 权重**

指定每个服务的权重比例，weight和访问比率成正比，通常用于后端服务机器性能不统一，将性能好的分配权重高来发挥服务器最大性能，如下配置后1702服务的访问频率会是1701服务的2倍。

```ini
upstream nginx_balance {
        server xxx.xxx.xxx.xxx:1701 weight=1;
        server xxx.xxx.xxx.xxx:1702 weight=2;
}
```

**[3] iphash**

每个请求都根据访问ip的hash结果分配，经过这样的处理，每个访客固定访问一个后端服务。

```ini
upstream nginx_balance {
			  ip_hash;
        server xxx.xxx.xxx.xxx:1701 weight=1;
        server xxx.xxx.xxx.xxx:1702 weight=2;
}
```

注意：配置之后，再访问主服务时，当前IP地址固定访问其中的一个地址，不会再发生变更了，ip_hash可以和weight配合使用。

**[4] 最少连接**

将请求分配到连接数最少的服务上

```ini
upstream nginx_balance {
			  least_conn;
        server xxx.xxx.xxx.xxx:1701 weight=1;
        server xxx.xxx.xxx.xxx:1702 weight=2;
}
```

**[5] fair服务器的响应时间来分配**

按后端服务器的响应时间来分配请求，响应时间短的优先分配。

```ini
upstream  nginx_balance {
        fair;
        server xxx.xxx.xxx.xxx:1701 weight=1;
        server xxx.xxx.xxx.xxx:1702 weight=2;
}
```

注意：若是未安装 upstream-fair 插件，重启nginx会报错，需要先安装之后再使用。