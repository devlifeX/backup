
# MySQL Automatic Backup 
This [Docker](https://hub.docker.com/r/devlifex/mysql-auto-backup/)
image helps you start your own MySQL Automatic Backup server, And Provide Report Over Telegram  


# How it work?
Run this docker image and at every time you set in `docker-compose.yml` The application connect to other server and got the database backup,
download the file and keep it untile they got old, after doing the job it will send Report message over Telegram so you can find the proccess was success or failuer, Of course on failure the human readable error provide.

# What is the limitions?
At this moment it can backup mysql database over docker at remot server and not mysql server it self. if you are running old fashion mysql server it won't help you. 

# Prerequsites
0. Dedicaed Server Or VPS 
1. Docker
2. Docker Compose
3. Telegram Bot Token and chat_id (Optional) 
- [Create bot Token](https://t.me/BotFather)
- [Find chat_id](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id)  
- Do NOT forget to add the bot to your group and promot it to Admin  
- NOTICE: If you want to recive Telegram notifications And your VPS host in Region that Telegram can not send message like IRAN or China..,! you have to buy another VPS In region that Telegram CAN, so [use this repo](https://github.com/yegor256/squid-proxy) to [setup and run the proxy](https://github.com/devlifeX/backup/edit/master/README.md#setup-telegram-proxy). 


# Quick Usage
First, you need to pull this repo:

```bash
git clone https://github.com/devlifeX/backup
```

Then write proper `servers.yml` file (Also You can use `servers.yml.sample` in this repo too)

```yml
options:
  sendAlertIfHardDiskUsageGoOverThisPercentage: 80
  telegram: 
    botToken: BOT_TOKEN
    chat_id: CHAT_ID
    disable_notification: true
    proxy:
      username: PROXY_USERNAME
      password: PROXY_PASSWORD
      hostname: PROXY_IP_ADDRESS
      port: PROXY_PORT
servers: # It's List Of Server Object
  - server1:
    project_name: "google"
    saveDir: /tmp/b/google
    keepCount: 4
    username: root
    hostname: YOUR_SERVER_IP_ADDRESS
    port: 22
    key: ~/.ssh/id_rsa
    mysql:
      container: "database"
      user: "root"
      pass: "root"
      database: "DATABASE_NAME"
      port: 3306
```

Notice: servers node is a List of Server Objects, It means you can add many server you have under it.

Then Edit `docker-compose.yml` and Change `CRONTAB` Enviroment to wahtever you want You can find [examples of Crontab Here](https://crontab.guru/examples.html)  

## Build Image
```bash
docker build . --tag=DOCKERHUB_USERNAME/NAME_OF_IMAGE --build-arg CRONTAB="\* \* \* \* \*"
```

## Setup Telegram Proxy 
Inside Your VPS Install Docker And run this command, That's it, now you can fiil-out the proxy section in `servers.yml` file.
```bash
docker run --name proxy -d --restart=always --publish 3128:3128 -e USERNAME=d1 -e PASSWORD=d1 yegor256/squid-proxy:0.1
```

Contributions are welcome, please send your PR :)
