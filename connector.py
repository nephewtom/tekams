import uuid
import requests
from stem import Signal
from stem.control import Controller


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
