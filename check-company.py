import re
import argparse
import requests

from stem import Signal
from stem.control import Controller


class Parser:
    def __init__(self, html):
        self.html = html

    def regex(self, exp):
        match = re.search(exp, self.html)
        value = match.group(1) if match else 'none'
        return value

    def get_business_name(self):
        name = self.regex('>Información de (.*) \| Guía Empresas</title><script>')
        print('name:', name)

    def get_address(self):
        address = self.regex('situation_calle">(.*)</span><li><strong>Localidad: ')
        print('address:', address)

    def get_city(self):
        city = self.regex('situation_loc">(.*)</span><li><strong>Provincia: ')
        print('city:', city)

    def get_phone(self):
        phone = self.regex('eacute;fono: </strong>(.*)<div')
        print('phone:', phone)

    def get_cnae(self):
        cnae = self.regex('<strong>CNAE: </strong>(.*)<li><strong>Objeto Social: ')
        print('cnae:', cnae)

    def get_billing(self):
        billing = self.regex('registrada: </strong>(.*)</p>')
        print('billing:', billing)

    def get_employees(self):
        employees = self.regex('registrado: </strong>(.*)</p>')
        print('employees:', employees)

    def get_info(self):
        self.get_business_name()
        self.get_address()
        self.get_city()
        self.get_phone()
        self.get_cnae()
        self.get_billing()
        self.get_employees()


class Getter:
    def __init__(self, url):
        self.session = self.__get_tor_session()
        self.url = url

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

    def get_ip(self):
        ip = self.session.get("http://icanhazip.com").text.rstrip()
        return ip

    def print_ip(self):
        print("[ ip:", self.ip, "]\n")

    def renew_ip(self):
        self.__renew_tor_session()
        ip = self.get_ip()
        while ip == self.ip:
            self.__renew_tor_session()

        self.ip = ip

    def get_company(self):
        html = self.session.get(self.url).text
        parser = Parser(html)
        parser.get_info()

    def run(self):
        self.ip = self.get_ip()
        self.print_ip()

        self.get_company()

        print("\n--- renew_ip ---")
        self.renew_ip()
        self.print_ip()

        self.get_company()


parser = argparse.ArgumentParser()
parser.add_argument("url", help="url")
args = parser.parse_args()

print("url:", args.url)

getter = Getter(args.url)
getter.run()
