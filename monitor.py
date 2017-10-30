import subprocess
import shlex
import time


def run_parallel():
        global parallel
        parallel = subprocess.Popen(['python', 'parallel.py'],
                                    shell=False, stdout=subprocess.PIPE)
        # parallel.communicate()
        # o = parallel.communicate()[0]
        # print(so)
        o = parallel.stdout.readline()
        so = str(o, 'UTF-8')
        print(so)


print("run_parallel()")
#run_parallel()
time.sleep(2)
print("while True")
while True:
    ps = subprocess.Popen(shlex.split('ps -ef'), stdout=subprocess.PIPE)
    grep = subprocess.Popen(shlex.split('grep parallel.py'), stdin=ps.stdout,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ps.stdout.close()
    out, err = grep.communicate()

    # print("out:{0}".format(out))
    # print("err:{0}".format(err))
    sout = str(out, 'UTF-8')
    nlines = len(sout.split("\n"))
    # print("lines:", nlines)
    if nlines == 2:
        print("Restarting parallel.py !!!")
        run_parallel()
    else:
        print("parallel.py processes are running")

    # print("Sleeping 5 secs")
    time.sleep(5)
