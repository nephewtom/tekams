import sys
import argparse

from record import Record
from database import Database
from connector import ConnectorDb
from page_parser import PageParser
from company_parser import CompanyParser


class Getter:
    def __init__(self, base_url):
        self.base_url = base_url
        self.db = Database('tekams')
        self.conn = ConnectorDb(self.db)
        self.all_records = []

    def __fill_record(self, url, record):
        html, uid = self.conn.get_html(url, True)
        parser = CompanyParser(html)
        parser.fill(record)
        return uid

    def __fill_company_info(self, record):
        renew = False
        url = self.base_url + record.name + ".html"
        uid = self.__fill_record(url, record)
        if record.phone == 'none':
            self.conn.renew_ip()
            uid = self.__fill_record(url, record)
            renew = True

        record.display()
        self.db.insert(uid, record, renew)

    def __check_captcha(self, url):
        html, uid = self.conn.get_html(url, False)
        res = html.find("ERROR_CAPADO_ROBOTS")
        captcha = (res != -1)
        return captcha, html, uid

    def __anti_captcha(self, url, page):
        captcha, html, uid = self.__check_captcha(url)
        if captcha:
            self.conn.renew_ip()
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

    mur = Getter('http://guiaempresas.universia.es/')
    mur.get_pages(args.start, args.end)  # From 1 - 4104 for Murcia


if __name__ == "__main__":
    main()
