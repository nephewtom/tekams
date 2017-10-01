import re
import sys
import uuid
import sqlite3
import argparse
from datetime import datetime

import requests
from stem import Signal
from stem.control import Controller


class Record:
    def __init__(self, page, ranking, name, province):
        self.page = page
        self.name = name.group(1)[1:]
        self.ranking = ranking.group(1).replace(".", "")
        self.province = province.group(1)

    def display(self):
        print('{:5d} | {:6d} | {:60s} | {:30s} | {:15s} | {:9s}'
              .format(int(self.page), int(self.ranking), self.name,
                      self.city, self.province, self.phone))

    @classmethod
    def display_header(self):
        print('{:5s} | {:6s} | {:60s} | {:30s} | {:15s} | {:9s}'
              .format("Page", "Rankin", "Name", "City", "Province", "Phone"))
        print('{:5s} | {:6s} | {:60s} | {:30s} | {:15s} | {:9s}'
              .format('-'*5, '-'*6, '-'*60, '-'*30, '-'*15, '-'*9))


class Database:
    def __init__(self, db_name):
        self.connection = sqlite3.connect("{}.db".format(db_name))
        self.cursor = self.connection.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS company \
        (uid text, page integer, ranking integer, name text, address text, \
        city text, province text, phone text, cnae text, \
        billing text, employees text, renew integer)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS captcha \
        (uid text, page integer, success integer, datetime datetime)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS conns \
        (uid text, ip text, url text, datetime datetime)")

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

    def conns(self, uid, ip, url):
        self.cursor.execute(
            "INSERT INTO conns(uid, ip, url, datetime) \
            VALUES(?,?,?,?)", [uid, ip, url, datetime.now()])
        self.connection.commit()


class CompanyParser:
    def __init__(self, html):
        self.html = html

    def __regex(self, exp):
        match = re.search(exp, self.html)
        value = match.group(1) if match else 'none'
        return value

    def __get_business_name(self):
        return self.__regex('>Información de (.*) \| Guía Empresas</title><script>')

    def __get_address(self):
        return self.__regex('situation_calle">(.*)</span><li><strong>Localidad: ')

    def __get_city(self):
        return self.__regex('situation_loc">(.*)</span><li><strong>Provincia: ')

    def __get_phone(self):
        return self.__regex('eacute;fono: </strong>(.*)<div')

    def __get_cnae(self):
        return self.__regex('<strong>CNAE: </strong>(.*)<li><strong>Objeto Social: ')

    def __get_billing(self):
        return self.__regex('registrada: </strong>(.*)</p>')

    def __get_employees(self):
        return self.__regex('registrado: </strong>(.*)</p>')

    def fill_record(self, r):
        r.name = self.__get_business_name()
        r.address = self.__get_address()
        r.city = self.__get_city()
        r.phone = self.__get_phone()
        r.cnae = self.__get_cnae()
        r.billing = self.__get_billing()
        r.employees = self.__get_employees()


class PageParser:
    def __init__(self, page):
        self.page = page

    def get_records(self, html):
        before, keyword, after = html.partition('ranking_einf')
        reduced, keyword, after = after.partition('pagination-centered')
        # print("REDUCED:", reduced)
        records = []
        list = reduced.split('numranking')
        for i in range(1, len(list)):
            ranking = re.search('">(.*)</span', list[i])
            name = re.search('href="(.*).html">', list[i])
            province = re.search('hidden">(.*)</td>', list[i])

            record = Record(self.page, ranking, name, province)
            records.append(record)

        return records


class Connector:
    def __init__(self, db):
        self.db = db
        self.session = self.__get_tor_session()
        self.ip = self.__get_ip()

    def __get_tor_session(self):
        session = requests.session()
        # Tor uses the 9050 port as the default socks port
        session.proxies = {'http':  'socks5://127.0.0.1:9050',
                           'https': 'socks5://127.0.0.1:9050'}
        return session

    def __renew_tor_session(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)
        self.session = self.__get_tor_session()

    def __get_ip(self):
        ip = self.session.get("http://icanhazip.com").text.rstrip()
        return ip

    def renew_ip(self, msg):
        ip = self.ip
        # print("Renewing ip:", ip, msg)
        while ip == self.ip:
            self.__renew_tor_session()
            ip = self.__get_ip()
        # print("Renewed ip:", ip)
        self.ip = ip

    def get_html(self, url):
        response = self.session.get(url)
        uid = uuid.uuid4().hex
        self.db.conns(uid, self.ip, url)
        return response.text, uid


class Getter:
    def __init__(self, base_url):
        self.base_url = base_url
        self.db = Database('tekams')
        self.conn = Connector(self.db)
        self.all_records = []

    def __fill_record(self, url, record):
        html, uid = self.conn.get_html(url)
        parser = CompanyParser(html)
        parser.fill_record(record)
        return uid

    def __fill_company_info(self, record):
        renew = False
        url = self.base_url + record.name + ".html"
        uid = self.__fill_record(url, record)
        if record.phone == 'none':
            self.conn.renew_ip("for company")
            uid = self.__fill_record(url, record)
            renew = True

        record.display()
        self.db.insert(uid, record, renew)

    def __check_captcha(self, url):
        html, uid = self.conn.get_html(url)
        res = html.find("ERROR_CAPADO_ROBOTS")
        captcha = (res != -1)
        return captcha, html, uid

    def __anti_captcha(self, url, page):
        captcha, html, uid = self.__check_captcha(url)
        if captcha:
            self.conn.renew_ip("for page")
            captcha, html, uid = self.__check_captcha(url)
            self.db.captcha(uid, page, not captcha)
        return html

    def __get_companies(self, url, page):
        html = self.__anti_captcha(url, page)
        parser = PageParser(page)
        records = parser.get_records(html)
        for record in records:
            self.__fill_company_info(record)

        self.all_records.extend(records)

    def get_pages(self, start, end):
        for page in range(start, end+1):
            url = self.base_url + 'provincia/MURCIA/?qPagina=' + str(page)
            print("\n===== Extracting page", page, "=====  URL:", url, "\n")
            Record.display_header()
            self.__get_companies(url, page)
        print("\n", '='*30, "FIN", '='*30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start", help="start-page", type=int)
    parser.add_argument("end", help="end-page", type=int)
    args = parser.parse_args()

    if args.end < args.start:
        print("Error: start-page [", args.start,
              "] MUST be lower or equal than end-page [", args.end, "]")
        sys.exit()

    base_url = 'http://guiaempresas.universia.es/'
    mur = Getter(base_url)
    print("Get companies from page", args.start, "to page", args.end)
    mur.get_pages(args.start, args.end)  # Till 4104


if __name__ == "__main__":
    main()
