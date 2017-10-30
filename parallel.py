import multiprocessing as mp
from datetime import datetime
import os
import time
import subprocess

from database import Database
from page_getter import Getter


db = Database('tekams')
base_url = 'http://guiaempresas.universia.es/'


def parallel(page):
    # start_time = datetime.now()
    # print("pid:", os.getpid(), "start:", page[0], "end:", page[1])

    getter = Getter(db, base_url)
    getter.pages(page[0], page[1])

    # end_time = datetime.now()
    # execution_time = end_time.timestamp() - start_time.timestamp()
    # print("pid:", os.getpid(), "Finito:", execution_time, "seg")
    pass


def foo(x):
    return 410*(x-1)+1, x*410


def get_max_pages(pairs):
    new_pairs = []
    for p in pairs:
        last = db.selectLastPage(int(p[1]))
        # print(p[0], "<", p[1], ":", last[0])
        if last[0] != p[1]-1:
            new_pairs.append((last[0], p[1]))
    return new_pairs


def run():
    pairs = []
    for i in list(range(1, 11)):
        pairs.append(foo(i))

    new_pairs = get_max_pages(pairs)

    msg = "Running in parallel:"
    msg += str(new_pairs)
    msg += "\n"
    print(msg)
    with open("restarts", "a") as myfile:
        myfile.write(msg)

    if len(new_pairs) == 0:
        print("kill monitor")
        subprocess.call(["pkill", '-9', '-f', 'monitor.py'])

    start_time = datetime.now()
    with mp.Pool(10) as pool:
        pool.map(parallel, new_pairs)

    end_time = datetime.now()
    execution_time = end_time.timestamp() - start_time.timestamp()
    #print("Total:", execution_time)


if __name__ == "__main__":
    run()
