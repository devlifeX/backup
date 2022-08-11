FROM python:3.9
WORKDIR /root

COPY baseclass.py main.py mysql_backup.py telegram.py requirements.txt servers.yml ./

RUN pip install -r requirements.txt
RUN pip install --ignore-installed six

RUN apt update && apt install -y cron

ARG CRONTAB

RUN echo "$CRONTAB python /root/main.py" >/etc/cron.d/backup
RUN chmod 0644 /etc/cron.d/backup
RUN crontab /etc/cron.d/backup
RUN touch /var/log/backup.log
RUN chmod 777 /var/log/backup.log

LABEL "Author"="Dariush Vesal"
LABEL "Author Email"="dariush.vesal@gmail.com"

COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

CMD ["bash", "entrypoint.sh"]
