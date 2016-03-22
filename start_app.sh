#!/usr/bin/env bash

if [[ $SMB_LOGIN && $SMB_PASSWORD && $MOUNT_FOLDER && $SMB_PATH ]];
then
 echo "Mounting device...";
 mount -t cifs $SMB_PATH $MOUNT_FOLDER -o user=$SMB_LOGIN,pass=$SMB_PASSWORD
else
 echo "SMB detail not found, not mounting network drive"
fi;

mkdir /root/.ssh && echo $PUBLIC_KEY > /root/.ssh/authorized_keys

/usr/sbin/sshd

python /app/main.py
