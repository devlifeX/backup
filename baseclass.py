from shutil import ExecError
import paramiko
import yaml
import os
from pathlib import Path
import string
import random
import psutil
import time
import traceback


class Base:
    options = {}
    servers = {}

    def __init__(self):
        self.options = {}
        self.servers = {}

        self.serverLoader()

    def serverLoader(self):
        serverFile = os.path.abspath(f"{Path(__file__).parent.absolute()}/servers.yml")

        if not os.path.exists(serverFile):
            return None

        with open(serverFile, "r") as stream:
            try:
                content = yaml.safe_load(stream)
                self.options = content["options"]
                self.servers = content["servers"]
                return self
            except yaml.YAMLError as exc:
                self.log("Please check private key path, server IP and Server Port")

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))

    def connectWithSSHKey(self, server):
        try:
            pkey = paramiko.RSAKey.from_private_key_file(
                filename=os.path.expanduser(server["key"])
            )
            args = {
                "hostname": server["hostname"],
                "username": server["username"],
                "pkey": pkey,
                "banner_timeout": 9999,
                "auth_timeout": 200,
                "timeout": 999,
            }

            if "port" in server:
                args["port"] = server["port"]

            client = paramiko.SSHClient()
            policy = paramiko.AutoAddPolicy()
            client.set_missing_host_key_policy(policy)
            client.connect(**args)
            return client
        except paramiko.ssh_exception.NoValidConnectionsError as err:
            self.log("Please check private key path, server IP and Server Port")
            return None

    def hardDiskNotificationHandler(self, telegram):
        try:
            threshold = self.options["sendAlertIfHardDiskUsageGoOverThisPercentage"]
            if self.getHardDiskUsage() >= threshold:
                telegram.send(f"Disk usage exceeded {self.getHardDiskUsage()}%", self)
        except Exception as e:
            print("Incorrect YML format")
            self.log("Incorrect YML format")
            telegram.send(f"Incorrect YML format", self)

    def getHardDiskUsage(self):
        obj_Disk = psutil.disk_usage("/")
        return obj_Disk.percent

    def dirTralingSlash(self, path):
        return path if not str(path).endswith("/") else path[:-1]

    def getSaveDir(self, server):
        try:
            dir = self.dirTralingSlash(server["saveDir"])
            if not os.path.exists(dir):
                Path(dir).mkdir(0o775, parents=True, exist_ok=True)

            return dir
        except Exception as e:
            self.log(e)

    def log(self, message):
        if len(str(message).strip()) <= 0:
            return
        timestr = time.strftime("%Y-%m-%d-%H-%M-%S")
        path = "/var/log/backup.log"
        f = open(path, "a")
        f.write(f"{message} - {timestr}\n")
        print(f"{message} - {timestr}\n")
        f.close()
