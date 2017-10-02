import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_name):
        self.connection = sqlite3.connect("{}.db".format(db_name))

        self.connection.execute("CREATE TABLE IF NOT EXISTS company \
        (uid text, page integer, ranking integer, name text, address text, \
        city text, province text, phone text, cnae text, \
        billing text, employees text, renew integer)")

        self.connection.execute("CREATE TABLE IF NOT EXISTS captcha \
        (uid text, page integer, success integer, datetime datetime)")

        self.connection.execute("CREATE TABLE IF NOT EXISTS conns \
        (uid text, query text, ip text, url text, datetime datetime)")

#        self.cursor.execute("CREATE TABLE IF NOT EXISTS parallel \
#        (start_page integer, end_page integer, execution_time)")

        self.connection.commit()
        self.cursor = self.connection.cursor()

    def __insert(self, uid, page, ranking, name, address, city, province,
                 phone, cnae, billing, employees, renew):
        self.cursor.execute(
            "INSERT INTO company(uid, page, ranking, name, address, city, \
            province, phone, cnae, billing, employees, renew) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            [uid, page, ranking, name, address, city,
             province, phone, cnae, billing, employees, renew])
        self.connection.commit()

    def insert(self, uid, record, renew):
        renew_int = 1 if renew else 0
        self.__insert(uid, record.page, record.ranking, record.name,
                      record.address, record.city, record.province,
                      record.phone, record.cnae, record.billing,
                      record.employees, renew_int)

    def captcha(self, uid, page, success):
        success_int = 1 if success else 0
        self.cursor.execute(
            "INSERT INTO captcha(uid, page, success, datetime) \
            VALUES(?,?,?,?)", [uid, page, success_int, datetime.now()])
        self.connection.commit()

    def conns(self, uid, query, ip, url):
        self.cursor.execute(
            "INSERT INTO conns(uid, query, ip, url, datetime) \
            VALUES(?,?,?,?,?)", [uid, query, ip, url, datetime.now()])
        self.connection.commit()
