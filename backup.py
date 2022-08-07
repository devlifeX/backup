#!/usr/bin/env python3

from calendar import c
from http import server
from multiprocessing import connection
import yaml
import paramiko
import os
import time
from pathlib import Path

def main():
    servers  = serverLoader()
    for server in servers['servers']:
       connection = connectWithSSHKey(server)
       backupMySQL(server, connection)

def serverLoader():
    with open(os.path.abspath(f"{Path(__file__).parent.absolute()}/servers.yml"), "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}


def connectWithSSHKey(server):
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


def isContainerExist(connection):
    # docker ps -f "name=db" | wc -l
    try:
        _stdin, stdout, _stderr = connection.exec_command("docker ps -f 'name=db' | wc -l")
        lines = str(stdout.read().decode()).strip()
        if lines == "2": 
            return True
        else:
            return False
    except error:
        print(error)

def backupMySQL(server, connection):
    try:
        isExist = isContainerExist(connection)
        if(isExist):
            cleanBeforeSart(server, connection)
            doExport(server, connection)
            gzipDatabse(server, connection)
            filename = renameDatabase(server, connection)
            SFTP(server, connection, filename)
        else:
            print( f"No Database container on {server['hostname']}")
        connection.close()
    except error:
        print(error)

def doExport(server, connection):
    try:
        c = server['mysql']
        command = f"docker exec -i {c['container']} mysqldump --port {c['port']} -u {c['user']} -p{c['pass']} {c['database']} > /tmp/{c['database']}.sql"
        _stdin, stdout, _stderr = connection.exec_command(command)
        lines = str(stdout.read().decode()).strip()
        err = str(_stderr.read().decode()).strip()
        print(err)
    except error:
        print(error)

def gzipDatabse(server, connection):
    try:
        c = server['mysql']
        command = f"gzip -9 /tmp/{c['database']}.sql"
        _stdin, stdout, _stderr = connection.exec_command(command)
        lines = str(stdout.read().decode()).strip()
        print(lines)
    except error:
        print(error)

def cleanBeforeSart(server, connection):
    try:
        c = server['mysql']
        command = f"sudo rm -rf /tmp/{c['database']}.sql"
        _stdin, stdout, _stderr = connection.exec_command(command)
        lines = str(stdout.read().decode()).strip()
        print(lines)
    except error:
        print(error)

def renameDatabase(server, connection):
    try:
        project_name = server['project_name']
        c = server['mysql']
        timestr = time.strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{project_name}-{c['database']}-{timestr}.sql.gz"
        command = f"mv /tmp/{c['database']}.sql.gz /tmp/{filename}"
        _stdin, stdout, _stderr = connection.exec_command(command)
        lines = str(stdout.read().decode()).strip()
        return filename
    except error:
        print(error)


def keepHandler(server):
    try:
        project_name = server['project_name']
        dir = server['saveDir']
        keepCount = server['keepCount']
        if(not os.path.exists(dir)):
            os.mkdir(dir)
             
        os.chdir(dir)
        files = sorted(filter(os.path.isfile, os.listdir(dir)), key=os.path.getmtime)

        count = 0
        for file in files:
            if(file.split("-")[0] == project_name):
                count+=1

        if(count >= keepCount):
           for i in range(0, count + 1 - keepCount):
                os.remove(f"{dir}/{files[i]}")

    except error:
        print(error)

def SFTP(server, connection, filename):
    keepHandler(server)
    sftp = connection.open_sftp()
    dir = server['saveDir']
    sftp.get(f"/tmp/{filename}", f"{dir}/{filename}")

def commandHandler(server, connection):
    try:
        if 'commands' not in server or server['commands'] is None:
            return "Done"

        for command in server['commands']:
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = stdout.read().decode()
            print(lines)
        connection.close()
    except paramiko.ssh_exception as  error:
        print(error)

if __name__ == '__main__':
    main()