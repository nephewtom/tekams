import re
from record import Record


class PageParser:
    def __init__(self, page):
        self.page = page

    def get_records(self, html):
        before, keyword, after = html.partition('ranking_einf')
        reduced, keyword, after = after.partition('pagination-centered')
        # print("REDUCED:", reduced)
        records = []
        list = reduced.split('numranking')
        for i in range(1, len(list)):
            ranking = re.search('">(.*)</span', list[i])
            name = re.search('href="(.*).html">', list[i])
            province = re.search('hidden">(.*)</td>', list[i])

            record = Record(self.page, ranking, name, province)
            records.append(record)

        return records
