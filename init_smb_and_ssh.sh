#!/bin/bash

if [[ $SMB_LOGIN && $SMB_PASSWORD && $MOUNT_FOLDER && $SMB_PATH ]];
then
 echo "Mounting device...";
 mount -t cifs $SMB_PATH $MOUNT_FOLDER -o user=$SMB_LOGIN,pass=$SMB_PASSWORD
else
 echo "SMB detail not found, not mounting network drive"
fi;

echo "Running ssh deamon";
/usr/sbin/sshd