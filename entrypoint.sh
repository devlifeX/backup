echo "$CRONTAB /usr/local/bin/python /root/main.py  >> /var/log/backup.log  2>&1" >/etc/cron.d/backup
