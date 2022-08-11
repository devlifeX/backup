FROM python:3.9
WORKDIR /root

COPY baseclass.py main.py mysql_backup.py telegram.py requirements.txt servers.yml ./

RUN pip install -r requirements.txt
RUN pip install --ignore-installed six

RUN apt update && apt install -y cron vim

ARG CRONTAB

RUN echo "0 * * * * /usr/local/bin/python /root/main.py  >> /var/log/backup.log" >/etc/cron.d/backup
RUN chmod 0644 /etc/cron.d/backup
RUN crontab /etc/cron.d/backup
RUN touch /var/log/backup.log
RUN chmod 777 /var/log/backup.log

LABEL "Author Name"="Dariush Vesal"
LABEL "Author Email"="dariush.vesal@gmail.com"

COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

RUN ln -sf /proc/1/fd/1 /var/log/backup.log

CMD bash entrypoint.sh && cron -f
