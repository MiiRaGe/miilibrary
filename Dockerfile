FROM resin/rpi-raspbian:wheezy-2015-01-15

RUN apt-get update && apt-get install -yq \
    openssh-server

RUN mkdir /var/run/sshd \
    && echo 'root:resin' | chpasswd \
    && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

RUN mkdir /root/.ssh && echo $PUBLIC_KEY > /root/.ssh/authorized_keys

RUN apt-get install -yq cifs-utils

RUN /app/init_smb_and_ssh.sh

RUN apt-get install -y python python-pip

COPY . /app

#RUN pip install -r /app/requirements.txt

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["python", "/app/main.py"]
