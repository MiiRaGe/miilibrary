#!/bin/sh

if [ $SMB_LOGIN != "" && $SMB_PASSWORD != "" && $MOUNT_FOLDER != "" && $SMB_PATH != "" ];
then
 echo "Mounting device...";
 mount -t cifs $SMB_PATH $MOUNT_FOLDER -o user=$SMB_LOGIN,pass=$SMB_PASSWORD
fi;

echo "Running ssh deamon";
/usr/sbin/sshd &