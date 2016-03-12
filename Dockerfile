FROM resin/rpi-raspbian:wheezy-2015-01-15

RUN sudo apt-get install sshd

CMD sshd