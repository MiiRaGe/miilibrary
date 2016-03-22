FROM resin/rpi-raspbian:latest

RUN apt-get update && apt-get install -yq python python-dev python-pip git python-setuptools \
    openssh-server cifs-utils build-essential \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd \
    && echo 'root:resin' | chpasswd \
    && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

COPY . /app

RUN pip install --upgrade setuptools

RUN pip install --no-input -r /app/requirements.txt

RUN ["/usr/sbin/sshd"]

WORKDIR /app

CMD ["/app/start_app.sh"]
