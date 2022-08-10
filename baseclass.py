import paramiko
import yaml
import os
from pathlib import Path
import string
import random
 
class Base:
    options = {}
    servers ={}

    def __init__(self):
        self.options = {}
        self.servers = {}
        self.serverLoader()
       

    def serverLoader(self):
        serverFile = os.path.abspath(f"{Path(__file__).parent.absolute()}/servers.yml")
        
        if (not os.path.exists(serverFile)):
            return None

        with open(serverFile, "r") as stream:
            try:
               content =  yaml.safe_load(stream)
               self.options = content['options']
               self.servers = content['servers']
               return self
            except yaml.YAMLError as exc:
                print(exc)
                return self

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def connectWithSSHKey(self, server):
        try:
            pkey = paramiko.RSAKey.from_private_key_file(filename=os.path.expanduser("~/.ssh/id_rsa"))
            args = {
            "hostname": server['hostname'],
            "username": server['username'],
            "pkey": pkey,
            }

            if('port' in server):
                args['port']  = server['port']

            client = paramiko.SSHClient()
            policy = paramiko.AutoAddPolicy()
            client.set_missing_host_key_policy(policy)
            client.connect(**args)
            return client
        except paramiko.ssh_exception.NoValidConnectionsError as err:
            print("Please check private key path, server IP and Server Port")
            return None
    