import argparse

from company_parser import CompanyParser
from connector import Connector


class Getter:
    def __init__(self, url):
        self.url = url
        self.conn = Connector()

    def get_company(self):
        html = self.conn.get_html(self.url)
        parser = CompanyParser(html)
        parser.print_info()

    def run(self):
        self.conn.print_ip()
        self.get_company()
        print("\n--- renew_ip ---")
        self.conn.renew_ip()
        self.conn.print_ip()
        self.get_company()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Company url to extract info")
    args = parser.parse_args()

    print("url:", args.url)

    getter = Getter(args.url)
    getter.run()


if __name__ == "__main__":
    main()
