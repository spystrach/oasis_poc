FROM nginxinc/nginx-unprivileged:alpine3.19-slim

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/nginx.conf
