from shutil import ExecError
from baseclass import Base
import os
import time
from telegram import Telegram


class Report:
    def __init__(self):
        self.log = {}

    def add(self, key, value):
        self.log[key] = value

    def error(self, key, value):
        self.log[key]['error'].append(value)

    def print(self):
        output = ""
        done = 0
        failed = 0
        for key, l in self.log.items():
            print(l)
            if (len(l['error']) <= 0):
                done += 1
                output += f"{l['project_name']}: successful\n"
            else:
                failed += 1
                output += f"\t{l['project_name']}: failed\n"
                for e in l['error']:
                    output += f"\t\t{e}\n"

        headline = f"Done: {done} - Failed: {failed}\n"
        return headline + output


class MysqlBackup:
    def __init__(self):
        self.base = Base()
        self.telegram = Telegram()
        self.report = Report()

    def run(self):
        self.base.hardDiskNotificationHandler(self.telegram)
        for server in self.base.servers:
            try:
                self.report.add(server['project_name'], {
                                "project_name": server['project_name'], "error": []})
                connection = self.base.connectWithSSHKey(server)
                if (connection is None):
                    self.base.log(
                        f"Failed to connect ro server {server['hostname']}")
                    self.report.error(server['project_name'],
                                      f"Failed to connect ro server {server['project_name']}")
                    continue
                self.backupMySQL(server, connection)
            except Exception as error:
                self.base.log(f"Error: Main Function: {error}")
                self.report.error(server['project_name'], error)

        self.telegram.send(self.report.print(), self.base)

    def isContainerExist(self, connection):
        # docker ps -f "name=db" | wc -l
        try:
            _stdin, stdout, _stderr = connection.exec_command(
                "docker ps -f 'name=db' | wc -l")
            lines = str(stdout.read().decode()).strip()
            if lines == "2":
                return True
            else:
                return False
        except:
            self.base.log("Error: isContainerExist")

    def backupMySQL(self, server, connection):
        try:
            self.base.log(f"Start on {server['hostname']}")
            isExist = self.isContainerExist(connection)
            if (isExist):
                self.cleanBeforeSart(server, connection)
                self.doExport(server, connection)
                self.gzipDatabse(server, connection)
                filename = self.renameDatabase(server, connection)
                self.SFTP(server, connection, filename)
                self.base.log(f"Finished on {server['hostname']}")
            else:
                self.base.log(f"No Database container on {server['hostname']}")
                self.report.error(server['project_name'],
                                  "Container not running!")
            connection.close()
        except:
            self.base.log("Error: backupMySQL")
            self.report.error(server['project_name'],
                              "Error: backupMySQL")

    def doExport(self, server, connection):
        try:
            c = server['mysql']
            command = f"echo \"{c['pass']}\" | docker exec -i {c['container']} mysqldump --single-transaction --quick --lock-tables=false --port {c['port']} -u {c['user']} -p {c['database']} > /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            err = str(_stderr.read().decode()).strip().replace(
                "Enter password:", "").strip()
            if (len(err) >= 0):
                self.report.error(server['project_name'],
                                  str(err).strip())
            self.base.log(err)
        except:
            self.base.log("Error: doExport")
            self.report.error(server['project_name'],
                              str(error).strip())

    def gzipDatabse(self, server, connection):
        try:
            c = server['mysql']
            command = f"gzip -9 /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            self.base.log(lines)
        except:
            self.base.log("Error: gzipDatabse")
            self.report.error(server['project_name'],
                              "Error: gzipDatabse")

    def cleanBeforeSart(self, server, connection):
        try:
            c = server['mysql']
            command = f"sudo rm -rf /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            self.base.log(lines)
        except:
            self.base.log("Error: cleanBeforeSart")
            self.report.error(server['project_name'],
                              "Error: cleanBeforeSart")

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
        except:
            self.base.log("Error: renameDatabase")
            self.report.error(server['project_name'],
                              "Error: renameDatabase")

    def keepHandler(self, server):
        try:
            project_nameAndDatabase = server['project_name'] + \
                "-" + server['mysql']['database']
            dir = server['saveDir']
            keepCount = server['keepCount']
            if (not os.path.exists(dir)):
                os.mkdir(dir)

            os.chdir(dir)
            files = sorted(
                filter(os.path.isfile, os.listdir(dir)), key=os.path.getmtime)

            backup_files = list(
                filter(lambda f, i=project_nameAndDatabase: (f.split("_")[0] == i), files))

            count = len(backup_files)
            if (count >= keepCount):
                for i in range(0, count + 1 - keepCount):
                    os.remove(f"{dir}/{backup_files[i]}")

        except:
            self.base.log("Error: keepHandler")
            self.report.error(server['project_name'],
                              "Error: keepHandler")

    def SFTP(self, server, connection, filename):
        try:
            self.keepHandler(server)
            sftp = connection.open_sftp()
            dir = server['saveDir']
            sftp.get(f"/tmp/{filename}", f"{dir}/{filename}")
            sftp.remove(f"/tmp/{filename}")
        except:
            self.base.log("Error: SFTP - transfer file")
            self.report.error(server['project_name'],
                              "Error: SFTP - transfer file")
