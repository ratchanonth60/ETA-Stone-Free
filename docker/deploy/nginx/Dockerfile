FROM nginxproxy/nginx-proxy

RUN mkdir -p /usr/src/django/src/static/
RUN mkdir -p /usr/src/django/src/media/

RUN rm /etc/nginx/conf.d/default.conf

COPY docker/deploy/nginx/nginx.conf /etc/nginx/conf.d
COPY docker/deploy/vhost.d/default /etc/nginx/vhost.d/default