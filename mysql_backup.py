from baseclass import Base
import os
import time

class MysqlBackup:
    def __init__(self):
        self.base = Base()

    def run(self):
        try:
            for server in self.base.servers:
                connection = self.base.connectWithSSHKey(server)
                if(connection is None):
                        print(f"Failed to connect ro server {server['hostname']}")
                        continue
                self.backupMySQL(server, connection)
        except error:
            print(error)

    def isContainerExist(self, connection):
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


    def backupMySQL(self, server, connection):
        try:
            print(f"Start on {server['hostname']}")
            isExist = self.isContainerExist(connection)
            if(isExist):
                self.cleanBeforeSart(server, connection)
                self.doExport(server, connection)
                self.gzipDatabse(server, connection)
                filename = self.renameDatabase(server, connection)
                self.SFTP(server, connection, filename)
                print(f"Finished on {server['hostname']}")
            else:
                print( f"No Database container on {server['hostname']}")
            connection.close()
        except error:
            print(error)

    def doExport(self, server, connection):
        try:
            c = server['mysql']
            command = f"docker exec -i {c['container']} mysqldump --single-transaction --quick --lock-tables=false --port {c['port']} -u {c['user']} -p{c['pass']} {c['database']} > /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            err = str(_stderr.read().decode()).strip()
            print(err)
        except error:
            print(error)

    def gzipDatabse(self, server, connection):
        try:
            c = server['mysql']
            command = f"gzip -9 /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            print(lines)
        except error:
            print(error)

    def cleanBeforeSart(self, server, connection):
        try:
            c = server['mysql']
            command = f"sudo rm -rf /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            print(lines)
        except error:
            print(error)

    def renameDatabase(self, server, connection):
        try:
            project_name = server['project_name']
            c = server['mysql']
            rndString = self.base.id_generator()
            timestr = time.strftime("%Y-%m-%d-%H-%M-%S")
            filename = f"{project_name}-{c['database']}_{rndString}-{timestr}.sql.gz"
            command = f"mv /tmp/{c['database']}.sql.gz /tmp/{filename}"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            return filename
        except error:
            print(error)


    def keepHandler(self, server):
        try:
            project_nameAndDatabase = server['project_name'] + "-"+ server['mysql']['database']
            dir = server['saveDir']
            keepCount = server['keepCount']
            if(not os.path.exists(dir)):
                os.mkdir(dir)
        
            os.chdir(dir)
            files = sorted(filter(os.path.isfile, os.listdir(dir)), key=os.path.getmtime)
        
            backup_files = list(filter(lambda f, i=project_nameAndDatabase:(f.split("_")[0] == i) , files))
                
            count = len(backup_files) 
            if(count >= keepCount):
                for i in range(0, count + 1 - keepCount):
                        os.remove(f"{dir}/{backup_files[i]}")
        
        except error:
            print(error)

    def SFTP(self, server, connection, filename):
        self.keepHandler(server)
        sftp = connection.open_sftp()
        dir = server['saveDir']
        sftp.get(f"/tmp/{filename}", f"{dir}/{filename}")