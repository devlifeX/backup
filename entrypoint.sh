echo "$CRONTAB python /root/main.py >> /var/log/backup.log" >/etc/cron.d/backup
cron && tail -f /var/log/backup.log
