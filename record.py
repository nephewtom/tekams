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
