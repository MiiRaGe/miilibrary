FROM resin/rpi-raspbian:latest

RUN apt-get update && apt-get install -yq python3 python3-dev python-pip git python-setuptools \
    openssh-server cifs-utils build-essential debconf-utils rabbitmq-server libmysqlclient-dev memcached libffi-dev \
    libssl-dev supervisor  rsyslog

RUN echo 'mysql-server mysql-server/root_password password root' | debconf-set-selections  \
		&& echo 'mysql-server mysql-server/root_password_again password root' | debconf-set-selections

RUN apt-get install -y nginx nginx-light

RUN apt-get install -y mysql-server && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN sed -i -e "s@^datadir.*@datadir = /data/mysql@" /etc/mysql/my.cnf

RUN mkdir /var/run/sshd \
    && echo 'root:resin' | chpasswd \
    && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

RUN pip3 install --upgrade setuptools

ADD requirements.txt /

RUN pip3 install -U --force-reinstall pip && pip install --no-input -r requirements.txt

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY . /app

WORKDIR /app

CMD ["/app/start_app.sh"]
