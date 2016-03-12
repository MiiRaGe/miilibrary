FROM resin/rpi-raspbian:wheezy-2015-01-15

RUN apt-get update && apt-get install -yq \
    openssh-server && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd \
    && echo 'root:resin' | chpasswd \
    && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

RUN mkdir /root/.ssh && echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC8Jh2kY2RDKiUoLcNCBnkglAaIsKnY+IfLus1ohhkcX5JZ8q9c0wUthskqg5i8GP2WNP5Ii1deGOBVlXHBkCXNiyVISbKbd9mWxAT+udBG1JZu9DhZKiTQc9t7z/kZLMvTuulXIehBWXZcEtm8eHyKTtwHH08R3TEUrvu6150KxfMEQSJHN7M3BA6Uf4g+6aU1UCp7mBlDYOMimR5AE4UiWJOOQo3zvyM25NxaHFFCtr+ArJaw+KTrMtLf7efY2xIPga75sKdGkm73JZZS1atIstYZRY7k2X1/WOdd9/0oRucqc9MPL/l2hmaoZYhQCgGknsxKJ6QkrlZWJaSGx3gV MiiRaGe@Alexiss-MacBook-Pro.local' > /root/.ssh/authorized_keys

RUN /usr/sbin/sshd

RUN apt-get update && apt-get install -y python

COPY . /app

#RUN pip install -r /app/requirements.txt

CMD ["python", "/app/main.py"]
