import multiprocessing as mp
from datetime import datetime
import os

from database import Database
from page_getter import Getter


db = Database('tekams')
base_url = 'http://guiaempresas.universia.es/'
getter = Getter(db, base_url)


def parallel(page):
    # start_time = datetime.now()
    print("pid:", os.getpid(), "start:", page[0], "end:", page[1])
    getter.pages(page[0], page[1])
    # end_time = datetime.now()
    # execution_time = end_time.timestamp() - start_time.timestamp()
    # print("pid:", os.getpid(), "Finito:", execution_time, "seg")


def foo(x):
    return x, x


def run():
    pairs = []
    for i in list(range(1, 11)):
        pairs.append(foo(i))
    print(pairs)
    start_time = datetime.now()
    with mp.Pool(10) as pool:
        print("with mp.Pool(10)")
        pool.map(parallel, pairs)

    end_time = datetime.now()
    execution_time = end_time.timestamp() - start_time.timestamp()
    print("Total:", execution_time)


if __name__ == "__main__":
    run()
