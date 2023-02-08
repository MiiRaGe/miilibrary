#!/usr/bin/env bash

if [[ $SMB_LOGIN && $SMB_PASSWORD && $MOUNT_FOLDER && $SMB_PATH ]];
then
 echo "Mounting device...";
 mount -t cifs $SMB_PATH $MOUNT_FOLDER -o user=$SMB_LOGIN,pass=$SMB_PASSWORD,vers=2.0
else
 echo "SMB detail not found, not mounting network drive"
fi;

echo "Starting memcached"
memcached -umemcache -d
echo "memcached started"

chmod 444 /etc/my.cnf.d/miilibrary.cnf
if [ ! -d /data/mysql ]; then
    echo "Creating mysql folder in persistent storage"
	mkdir -p /data/mysql
	cp -r /var/lib/mysql/* /data/mysql
	rm -rf /var/lib/mysql
    mysql_install_db --user=mysql
fi

echo "Making sure the user and config is correct for mysqld"
chown -R mysql:mysql /data/mysql
echo "Starting Mysql"
MYSQL=`which mysql`
/usr/bin/mysqld_safe&

OUTPUT="Can't connect"
while [[ $OUTPUT == *"Can't connect"* ]]
do
    OUTPUT=$($MYSQL -uroot -proot -e "FLUSH PRIVILEGES;" 2>&1)
	echo "Trying to connect to mysql..."
	sleep 1
done
echo "Mysql Started"

echo "Creating db and user if not exist"

Q1="CREATE DATABASE IF NOT EXISTS $DB_NAME;"
Q2="GRANT ALL ON *.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';"
Q2="GRANT ALL ON *.* TO '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
Q3="FLUSH PRIVILEGES;"
SQL="${Q1}${Q2}${Q3}"

$MYSQL -uroot -proot -e "$SQL"
echo "User created"

echo "Starting rabbitmq"
rabbitmq-server &
echo "Rabbitmq started"

echo "Configuring nginx"
if [ -f /etc/nginx/http.d/default.conf ];
then
	rm -f /etc/nginx/http.d/default.conf;
fi

if [ ! -f /etc/nginx/http.d/miilibrary.conf ]; then
	cd /etc/nginx/http.d && mv /app/miilibrary.nginx miilibrary.conf;
fi

nginx
echo "Nginx Started"

cd /app

echo "Static File"
python /app/manage.py collectstatic --noinput

echo "Running migrations"
python /app/manage.py migrate

echo "Starting main app"
supervisord -c /etc/supervisord.conf
