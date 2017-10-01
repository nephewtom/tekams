import re


class CompanyParser:
    def __init__(self, html):
        self.html = html

    def __regex(self, exp):
        match = re.search(exp, self.html)
        value = match.group(1) if match else 'none'
        return value

    def __special_chars(self, s):
        s = s.replace('&euro;', '€')
        s = s.replace('&aacute;', 'á')
        s = s.replace('&eacute;', 'é')
        s = s.replace('&iacute;', 'í')
        s = s.replace('&oacute;', 'ó')
        s = s.replace('&uacute;', 'ú')
        return s

    def __get_business_name(self):
        x = self.__regex('>Información de (.*) \| Guía Empresas</title><script>')
        return self.__special_chars(x)

    def __get_address(self):
        x = self.__regex('situation_calle">(.*)</span><li><strong>Localidad: ')
        return self.__special_chars(x)

    def __get_city(self):
        x = self.__regex('situation_loc">(.*)</span><li><strong>Provincia: ')
        return self.__special_chars(x)

    def __get_phone(self):
        x = self.__regex('eacute;fono: </strong>(.*)<div')
        return self.__special_chars(x)

    def __get_cnae(self):
        x = self.__regex('<strong>CNAE: </strong>(.*)<li><strong>Objeto Social: ')
        return self.__special_chars(x)

    def __get_billing(self):
        x = self.__regex('registrada: </strong>(.*)</p>')
        return self.__special_chars(x)

    def __get_employees(self):
        x = self.__regex('registrado: </strong>(.*)</p>')
        return self.__special_chars(x)

    def fill_record(self, r):
        r.name = self.__get_business_name()
        r.address = self.__get_address()
        r.city = self.__get_city()
        r.phone = self.__get_phone()
        r.cnae = self.__get_cnae()
        r.billing = self.__get_billing()
        r.employees = self.__get_employees()
