FROM resin/rpi-raspbian:wheezy-2015-01-15

RUN apt-get install -y openssh-server

CMD sshd