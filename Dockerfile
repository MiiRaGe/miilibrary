FROM resin/rpi-raspbian:wheezy-2015-01-15

RUN apt-get update && apt-get install -yq python python-pip git python-setuptools \
    openssh-server cifs-utils

RUN mkdir /var/run/sshd \
    && echo 'root:resin' | chpasswd \
    && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

RUN mkdir /root/.ssh && echo $PUBLIC_KEY > /root/.ssh/authorized_keys

COPY . /app

RUN pip install --no-input -r /app/requirements.txt

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["/app/init_smb.sh"]

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

CMV ["python", "/app/main.py"]
