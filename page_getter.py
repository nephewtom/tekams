import sys
import argparse
import uuid

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

    def __fill_record(self, url, record, query, uid):
        html = self.conn.get_html(url, query, uid)
        parser = CompanyParser(html)
        parser.fill(record)

    def __fill_company_info(self, record):
        uid = uuid.uuid4().hex
        status = 'first'
        url = self.base_url + record.name + ".html"
        self.__fill_record(url, record, status, uid)

        # Creo que el siguient if no aporta nada, de acuerdo con estos resultados:
        # sqlite> select count(*) from company where status = 'renew-phone' and phone = 'none';
        # 1378
        # sqlite> select count(*) from company where status = 'renew-phone';
        # 1378
        # if record.phone == 'none' and record.name != 'none':
        #     self.conn.renew_ip()
        #     status = 'renew-phone'
        #     self.__fill_record(url, record, status, uid)

        tries = 1
        while record.name == 'none' and tries < 11:
            self.conn.renew_ip()
            status = 'renew-name' + str(tries)
            self.__fill_record(url, record, status, uid)
            tries += 1

        self.db.insert(uid, record, status)

    def __check_captcha(self, url, uid):
        html = self.conn.get_html(url, 'page', uid)
        res = html.find("ERROR_CAPADO_ROBOTS")
        captcha = (res != -1)
        return captcha, html

    def __anti_captcha(self, url, page):
        uid = uuid.uuid4().hex
        captcha, html = self.__check_captcha(url, uid)
        tries = 5
        while captcha and tries > 0:
            self.conn.renew_ip()
            captcha, html = self.__check_captcha(url, uid)
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
                print("EXCEPTION fill_company_info BEGIN")
                record.display()
                print("EXCEPTION fill_company_info END")
                self.db.insert('666', record, 'FAILED')

    def pages(self, start, end):
        for page in range(start, end + 1):
            url = self.base_url + 'provincia/MURCIA/?qPagina=' + str(page)
            print("\n===== Extracting page", page, "=====  URL:", url, "\n")
            Record.display_header()
            self.__get_companies(url, page)
        print("\n", '=' * 30, "FIN", '=' * 30)


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
