import sys
import argparse

from record import Record
from database import Database
from connector import ConnectorDb
from page_parser import PageParser
from company_parser import CompanyParser


class Getter:
    def __init__(self, db, url):
        self.db = db
        self.conn = ConnectorDb(db)
        self.base_url = url

    def __fill_record(self, url, record, query):
        html, uid = self.conn.get_html(url, query)
        parser = CompanyParser(html)
        parser.fill(record)
        return uid

    def __fill_company_info(self, record):
        status = 'first'
        url = self.base_url + record.name + ".html"
        uid = self.__fill_record(url, record, status)

        if record.phone == 'none' and record.name != 'none':
            self.conn.renew_ip()
            status = 'renew-phone'
            uid = self.__fill_record(url, record, status)

        tries = 1
        while record.name == 'none' and tries < 6:
            self.conn.renew_ip()
            status = 'renew-name' + str(tries)
            uid = self.__fill_record(url, record, status)
            tries += 1

        self.db.insert(uid, record, status)

    def __check_captcha(self, url):
        html, uid = self.conn.get_html(url, 'page')
        res = html.find("ERROR_CAPADO_ROBOTS")
        captcha = (res != -1)
        return captcha, html, uid

    def __anti_captcha(self, url, page):
        captcha, html, uid = self.__check_captcha(url)
        tries = 5
        while captcha and tries > 0:
            self.conn.renew_ip()
            captcha, html, uid = self.__check_captcha(url)
            tries -= 1

        if captcha:  # Save page to try manually
            self.db.captcha(uid, page, not captcha)
        return html

    def __get_companies(self, url, page):
        html = self.__anti_captcha(url, page)
        parser = PageParser(page)
        records = parser.get_records(html)
        for record in records:
            try:
                self.__fill_company_info(record)
                record.display()
            except:
                self.db.insert('666', record, 'FAILED')

    def pages(self, start, end):
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

    url = 'http://guiaempresas.universia.es/'
    db = Database('tekams')
    getter = Getter(db, url)
    getter.pages(args.start, args.end)  # From 1 - 4104 for Murcia


if __name__ == "__main__":
    main()
