from shutil import ExecError
from baseclass import Base
import os
import time
from telegram import Telegram


class Report:
    def __init__(self):
        self.log = {}

    def add(self, key, value):
        if (value is None):
            return
        self.log[key] = value

    def error(self, key, value):
        if (len(str(value).strip())):
            return
        self.log[key]['error'].append(str(value).strip())

    def print(self):
        output = ""
        done = 0
        failed = 0
        for key, l in self.log.items():
            if (len(l['error']) <= 0):
                done += 1
                output += f"{l['project_name']}: Successful\n"
            else:
                failed += 1
                output += f"{l['project_name']}: Failed:\n"
                for e in l['error']:
                    output += f"{e}"

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
        except Exception as error:
            self.base.log(f"Error: isContainerExist: {error}")

    def backupMySQL(self, server, connection):
        try:
            self.base.log(f"Start on {server['project_name']}")
            isExist = self.isContainerExist(connection)
            if (isExist):
                self.cleanBeforeSart(server, connection)
                self.doExport(server, connection)
                self.gzipDatabse(server, connection)
                filename = self.renameDatabase(server, connection)
                self.SFTP(server, connection, filename)
                self.base.log(f"Finished on {server['project_name']}")
            else:
                self.base.log(
                    f"No Database container on {server['project_name']}")
                self.report.error(server['project_name'],
                                  "Container not running!")
            connection.close()
        except Exception as error:
            self.base.log(f"Error: backupMySQL {error}")
            self.report.error(server['project_name'],
                              f"Error: backupMySQL {error}")

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
        except Exception as error:
            self.base.log(f"Error: doExport {error}")
            self.report.error(server['project_name'],
                              error)

    def gzipDatabse(self, server, connection):
        try:
            c = server['mysql']
            command = f"gzip -9 /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            self.base.log(lines)
        except Exception as error:
            self.base.log(f"Error: gzipDatabse {error}")
            self.report.error(server['project_name'],
                              f"Error: gzipDatabse: {error}")

    def cleanBeforeSart(self, server, connection):
        try:
            c = server['mysql']
            command = f"sudo rm -rf /tmp/{c['database']}.sql"
            _stdin, stdout, _stderr = connection.exec_command(command)
            lines = str(stdout.read().decode()).strip()
            self.base.log(lines)
        except Exception as error:
            self.base.log(f"Error: cleanBeforeSart: {error}")
            self.report.error(server['project_name'],
                              f"Error: cleanBeforeSart: {error}")

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
        except Exception as error:
            self.base.log(f"Error: renameDatabase: {error}")
            self.report.error(server['project_name'],
                              f"Error: renameDatabase: {error}")

    def keepHandler(self, server):
        try:
            project_nameAndDatabase = server['project_name'] + \
                "-" + server['mysql']['database']
            dir = self.base.getSaveDir(server)
            keepCount = server['keepCount']
            print(dir)
            os.chdir(dir)
            files = sorted(
                filter(os.path.isfile, os.listdir(dir)), key=os.path.getmtime)

            backup_files = list(
                filter(lambda f, i=project_nameAndDatabase: (f.split("_")[0] == i), files))

            count = len(backup_files)
            if (count >= keepCount):
                for i in range(0, count + 1 - keepCount):
                    os.remove(f"{dir}/{backup_files[i]}")

        except Exception as error:
            self.base.log(f"Error: keepHandler: {error}")
            self.report.error(server['project_name'],
                              f"Error: keepHandler: {error}")

    def SFTP(self, server, connection, filename):
        try:
            self.keepHandler(server)
            sftp = connection.open_sftp()
            dir = self.base.getSaveDir(server)
            sftp.get(f"/tmp/{filename}", f"{dir}/{filename}")
            sftp.remove(f"/tmp/{filename}")
        except Exception as error:
            self.base.log(f"Error: SFTP - transfer file: {error}")
            self.report.error(server['project_name'],
                              f"Error: SFTP - transfer file {error}")
