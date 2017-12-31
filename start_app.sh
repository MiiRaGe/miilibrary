#!/usr/bin/env bash

if [[ $SMB_LOGIN && $SMB_PASSWORD && $MOUNT_FOLDER && $SMB_PATH ]];
then
 echo "Mounting device...";
 mount -t cifs $SMB_PATH $MOUNT_FOLDER -o user=$SMB_LOGIN,pass=$SMB_PASSWORD
else
 echo "SMB detail not found, not mounting network drive"
fi;

echo "Starting memcached"
memcached -u memcache -d
echo "memcached started"

if [ ! -d /data/mysql ]; then
    echo "Creating mysql folder in persistent storage"
	mkdir -p /data/mysql
	cp -r /var/lib/mysql/* /data/mysql
	rm -rf /var/lib/mysql
fi

echo "Making sure the user is correct for mysqld"
chown -R mysql:mysql /data/mysql
echo "Starting Mysql"
service mysql start
echo "Mysql Started"

echo "Creating db and user if not exist"
MYSQL=`which mysql`

Q1="CREATE DATABASE IF NOT EXISTS $DB_NAME;"
Q2="GRANT ALL ON *.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';"
Q3="FLUSH PRIVILEGES;"
SQL="${Q1}${Q2}${Q3}"

$MYSQL -uroot -proot -e "$SQL"
echo "User created"

echo "Starting rabbitmq"
rabbitmq-server &
echo "Rabbitmq started"

echo "Configuring nginx"
if [ -f /etc/nginx/sites-enabled/default ];
then
	rm -f /etc/nginx/sites-enabled/default;
fi

if [ ! -f /etc/nginx/sites-available/miilibrary ]; then
	cd /etc/nginx/sites-available && mv /app/miilibrary.nginx miilibrary;
fi

cd /etc/nginx/sites-enabled && ln -sf ../sites-available/miilibrary miilibrary;

service nginx start
echo "Nginx Started"

cd /app

echo "Static File"
python /app/manage.py collectstatic --noinput

echo "Running migrations"
python /app/manage.py migrate

echo "Starting main app"
supervisord -c /etc/supervisor/supervisord.conf
