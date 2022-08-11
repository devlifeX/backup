echo "$CRONTAB /usr/local/bin/python /root/main.py  >> /var/log/backup.log" >/etc/cron.d/backup
crontab /etc/cron.d/backup
