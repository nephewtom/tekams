import re
import sys
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


class CompanyDatabase:
    def __init__(self, db_name):
        self.connection = sqlite3.connect("{}.db".format(db_name))
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS company \
        (id datetime, page integer, ranking integer, name text, \
        address text, city text, province text, phone text, cnae text, \
        billing text, employees text, url text)")

    def __insert(self, page, ranking, name, address, city, province,
                 phone, cnae, billing, employees, url):
        self.cursor.execute(
            "INSERT INTO company(id, page, ranking, name, address, city, \
            province, phone, cnae, billing, employees, url) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            [datetime.now(), page, ranking, name, address, city, province,
             phone, cnae, billing, employees, url])
        self.connection.commit()

    def insert(self, r, url):
        self.__insert(r.page, r.ranking, r.name, r.address, r.city, r.province,
                      r.phone, r.cnae, r.billing, r.employees, url)


class CompanyParser:
    def __init__(self, html):
        self.html = html

    def regex(self, exp):
        match = re.search(exp, self.html)
        value = match.group(1) if match else 'none'
        return value

    def get_business_name(self):
        return self.regex('>Información de (.*) \| Guía Empresas</title><script>')

    def get_address(self):
        return self.regex('situation_calle">(.*)</span><li><strong>Localidad: ')

    def get_city(self):
        return self.regex('situation_loc">(.*)</span><li><strong>Provincia: ')

    def get_phone(self):
        return self.regex('eacute;fono: </strong>(.*)<div')

    def get_cnae(self):
        return self.regex('<strong>CNAE: </strong>(.*)<li><strong>Objeto Social: ')

    def get_billing(self):
        return self.regex('registrada: </strong>(.*)</p>')

    def get_employees(self):
        return self.regex('registrado: </strong>(.*)</p>')

    def fill_record(self, r):
        r.name = self.get_business_name()
        r.address = self.get_address()
        r.city = self.get_city()
        r.phone = self.get_phone()
        r.cnae = self.get_cnae()
        r.billing = self.get_billing()
        r.employees = self.get_employees()


class PageParser():
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


class Getter:
    def __init__(self, base_url):
        self.base_url = base_url
        self.all_records = []
        self.db = CompanyDatabase('tekams')
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

    def __renew_ip(self, msg):
        ip = self.ip
        print("Renewing ip:", ip, msg)
        while ip == self.ip:
            self.__renew_tor_session()
            ip = self.__get_ip()

        print("Renewed ip:", ip)
        self.ip = ip

    def get_html(self, url):
        response = self.session.get(url)
        return response.text

    def fill_record(self, url, record):
        html = self.get_html(url)
        parser = CompanyParser(html)
        record = parser.fill_record(record)

    def fill_company_info(self, record):
        url = self.base_url + record.name + ".html"
        self.fill_record(url, record)
        if record.phone == 'none':
            self.__renew_ip("for company")
            self.fill_record(url, record)

        record.display()
        self.db.insert(record, url)

    def anti_captcha(self, url):
        html = self.get_html(url)
        res = html.find("ERROR_CAPADO_ROBOTS")
        captcha = res != -1
        if captcha:
            self.__renew_ip("for page")
            html = self.get_html(url)

        return html

    def get_companies(self, url, page):
        html = self.anti_captcha(url)
        parser = PageParser(page)
        records = parser.get_records(html)
        for record in records:
            self.fill_company_info(record)

        self.all_records.extend(records)

    def get_pages(self, start, end):
        for page in range(start, end+1):
            url = self.base_url + 'provincia/MURCIA/?qPagina=' + str(page)
            print("\n===== Extracting page", page, "=====  URL:", url, "\n")
            Record.display_header()
            self.get_companies(url, page)

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
