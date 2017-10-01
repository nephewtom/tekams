import re
import sys
import sqlite3
import argparse
from datetime import datetime

import requests
from stem import Signal
from stem.control import Controller


class Record:

    def __init__(self, page, ranking, name, city, province):
        self.page = page
        self.ranking = ranking.group(1).replace(".", "")
        self.name = name.group(1)[1:]
        self.city = city.group(1)
        self.province = province.group(1)

    def display(self):
        print('{:4d} | {:6d} | {:50s} | {:30s} | {:15s} | {:9s}'.format(int(self.page), int(self.ranking), self.name, self.city, self.province, self.phone))


class CompanyDatabase:

    def __init__(self, db_name):
        self.connection = sqlite3.connect("{}.db".format(db_name))
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS company (id datetime, page integer, ranking integer, name text, city text, province text, phone text, url text)")

    def __insert(self, page, ranking, name, city, province, phone, url):
        self.cursor.execute(
            "INSERT INTO "
            "company(id, page, ranking, name, city, province, phone, url) "
            "VALUES(?,?,?,?,?,?,?,?)",
            [datetime.now(), page, ranking, name, city, province, phone, url])
        self.connection.commit()

    def insert(self, r, url):
        self.__insert(r.page, r.ranking, r.name, r.city, r.province, r.phone, url)


class Getter:
    def __init__(self, base_url):
        self.base_url = base_url
        self.all_records = []
        self.db = CompanyDatabase('tekams')
        self.session = self.get_tor_session()

    def get_tor_session(self):
        session = requests.session()
        # Tor uses the 9050 port as the default socks port
        session.proxies = {'http':  'socks5://127.0.0.1:9050',
                           'https': 'socks5://127.0.0.1:9050'}
        return session

    def renew_tor_session(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)

        self.session = self.get_tor_session()

    def __get_requests(self, url):
        # print(self.session.get("http://httpbin.org/ip").text)
        response = self.session.get(url)
        return response.text

    def getHtml(self, url):
        return self.__get_requests(url)

    def fillPhones(self, records):
        for record in records:
            url = self.base_url+record.name+".html"

            tries = 10
            record.phone = "sin telef"
            while tries > 0:
                # print("phone-tries:", tries)
                html = self.getHtml(url)
                phone = re.search('eacute;fono: </strong>(.*)<div', html)
                if phone:
                    record.phone = phone.group(1)
                    break

                tries -= 1
                self.renew_tor_session()

            self.db.insert(record, url)
            # print('ranking:', record.ranking)
            record.display()

        return records

    def getCompanyList(self, url, page):
        tries = 10
        while tries > 0:
            # print("tries:", tries)
            html = self.getHtml(url)
            # print("HTML:", html)
            res = html.find("ERROR_CAPADO_ROBOTS")
            if res != -1:
                print("CAPADO!")
                tries -= 1
                self.renew_tor_session()
            else:
                break

        before, keyword, after = html.partition('ranking_einf')
        reduced, keyword, after = after.partition('pagination-centered')
        # print("REDUCED:", reduced)
        records = []
        list = reduced.split('numranking')
        for i in range(1, len(list)):
            ranking = re.search('">(.*)</span', list[i])
            name = re.search('href="(.*).html">', list[i])
            city = re.search('<td>(.*)</td><td ', list[i])
            province = re.search('hidden">(.*)</td>', list[i])

            record = Record(page, ranking, name, city, province)
            records.append(record)

        records = self.fillPhones(records)
        self.all_records.extend(records)

    def getCompanyPages(self, start, end):
        for page in range(start, end+1):
            url = self.base_url + 'provincia/MURCIA/?qPagina=' + str(page)
            print("\n===== Extracting page", page, "=====  URL:", url, "\n")
            print('{:4s} | {:6s} | {:50s} | {:30s} | {:15s} | {:9s}'.format("Page", "Rankin", "Name", "City", "Province", "Phone"))
            print('{:4s} | {:6s} | {:50s} | {:30s} | {:15s} | {:9s}'.format("----", "------", "----", "----", "--------", "-----"))
            self.getCompanyList(url, page)

        print("\n========================= FIN ==============================")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start", help="start page", type=int)
    parser.add_argument("end", help="end page", type=int)
    args = parser.parse_args()

    if args.end < args.start:
        print("Error: start page", args.start, "MUST be lower than end page", args.end)
        sys.exit()

    base_url = 'http://guiaempresas.universia.es/'
    mur = Getter(base_url)
    print("Get companies from page", args.start, "to page", args.end)
    mur.getCompanyPages(args.start, args.end)  # Till 4104

#    for record in mur.all_records:
#        record.display()


if __name__ == "__main__":
    main()
