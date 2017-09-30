import re
import argparse
import requests

from stem import Signal
from stem.control import Controller


class PhoneGetter:
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

    def get_phone(self):
        html = self.session.get(self.url).text
        phone = re.search('eacute;fono: </strong>(.*)<div', html)
        print('phone:', end='')
        print(phone.group(1)) if phone else print("none")

    def renew_ip(self):
        self.__renew_tor_session()
        ip = self.get_ip()
        while ip == self.ip:
            self.__renew_tor_session()

        self.ip = ip

    def run(self):
        self.ip = self.get_ip()
        print("ip:", self.ip)

        self.get_phone()

        print("--- renew_ip ---")
        self.renew_ip()
        print("ip:", self.ip)

        self.get_phone()

parser = argparse.ArgumentParser()
parser.add_argument("url", help="url")
args = parser.parse_args()

print("url:", args.url)

getter = PhoneGetter(args.url)
getter.run()
