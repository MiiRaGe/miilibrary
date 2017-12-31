FROM resin/raspberrypi2-python:3.5.2

RUN apt-get update && apt-get install -yq openssh-server cifs-utils build-essential debconf-utils rabbitmq-server libmysqlclient-dev memcached libffi-dev \
    libssl-dev supervisor  rsyslog

RUN echo 'mysql-server mysql-server/root_password password root' | debconf-set-selections  \
		&& echo 'mysql-server mysql-server/root_password_again password root' | debconf-set-selections

RUN apt-get install -y nginx nginx-light

RUN apt-get install -y mysql-server && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN sed -i -e "s@^datadir.*@datadir = /data/mysql@" /etc/mysql/my.cnf

ADD requirements.txt /

RUN pip install --no-input -r requirements.txt

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY . /app

WORKDIR /app

CMD ["/app/start_app.sh"]
