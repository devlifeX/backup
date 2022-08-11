FROM python:3.9
WORKDIR /root
COPY baseclass.py main.py mysql_backup.py telegram.py requirements.txt servers.yml ./
RUN pip install -r requirements.txt
RUN pip install --ignore-installed six
# CMD [ "python", "./main.py" ]
ENTRYPOINT ["tail", "-f", "/dev/null"]
