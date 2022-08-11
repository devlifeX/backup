docker build . --tag=devlifex/mysql-auto-backup --build-arg CRONTAB="\* \* \* \* \*"

docker run --name proxy -d --restart=always --publish 3128:3128 -e USERNAME=d1 -e PASSWORD=d1 yegor256/squid-proxy:0.1
