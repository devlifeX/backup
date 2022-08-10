from mysql_backup import MysqlBackup


def main():
    backup = MysqlBackup()
    backup.run()


if __name__ == '__main__':
    main()
