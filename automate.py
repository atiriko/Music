import subprocess
import os
import signal
import time


while True:
    pro = subprocess.Popen(["powershell.exe", 
                      f'python main.py'], stdout=subprocess.DEVNULL,stdin = subprocess.PIPE, 
                               shell=False)
    time.sleep(5)

    pro.send_signal(signal.CTRL_C_EVENT)
    pro.stdin.write(b"q\n")
    pro.send_signal(signal.SIGTERM)
    pro.terminate()
    os.system('cls')