FROM balenalib/raspberry-pi2-alpine-python:latest

RUN install_packages openssh-server cifs-utils build-base git mariadb-dev memcached libffi-dev \
    openssl-dev supervisor rsyslog

RUN apk add rabbitmq-server --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/

RUN install_packages nginx

RUN install_packages mariadb

RUN sed -i -e "s@^skip-networking@skip-networking\ndatadir = /data/mysql@" /etc/my.cnf.d/mariadb-server.cnf

ADD requirements.txt /

RUN install_packages cargo rust

RUN pip install --upgrade pip && pip install --no-input --upgrade --force-reinstall -r requirements.txt
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY . /app

RUN chmod 755 /app/start_app.sh

WORKDIR /app

CMD ["/app/start_app.sh"]
