FROM balenalib/raspberry-pi2-alpine-python:latest

RUN install_packages openssh-server cifs-utils build-base git mariadb-dev memcached libffi-dev \
    openssl-dev supervisor rsyslog openrc nginx mariadb cargo rust mysql-client

RUN apk add rabbitmq-server --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/

ADD requirements.txt /

RUN pip install --upgrade pip && pip install --no-input --upgrade --force-reinstall -r requirements.txt

COPY miilibrary.cnf /etc/my.cnf.d/miilibrary.cnf

RUN chmod 222 /etc/my.cnf.d/miilibrary.cnf

RUN mysql_install_db --user=mysql

RUN useradd -ms /bin/bash memcache

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY . /app

RUN chmod 755 /app/start_app.sh

WORKDIR /app

CMD ["/app/start_app.sh"]
