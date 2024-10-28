import pyaudio
import wave
import os
import signal
import subprocess
import time
import datetime

# The os.setsid() is passed in the argument preexec_fn so
# it's run after the fork() and before  exec() to run the shell.
class Record():
    def __init__(self):
        self.pro = None
    def startRecording(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.pro = subprocess.Popen(["powershell.exe", 
                  f'ffmpeg -y -f gdigrab -framerate 30 -s 990x600 -i title="Composer"  -c:v libx264 recordings/output{now}.mp4 -f dshow -i audio="Stereo Mix (Realtek(R) Audio)" recordings/output{now}.mp4'], stdout=subprocess.DEVNULL,stdin = subprocess.PIPE, 
                           shell=False)

    
    def stopRecording(self):
        # pro.send_signal(signal.CTRL_C_EVENT)
        self.pro.stdin.write(b"q\n")
        time.sleep(2)
        self.pro.stdin.write(b"\n")
        # self.pro.stdin.close()
        self.pro.terminate()
        time.sleep(2)
        os.system('cls')
    
if __name__ == "__main__":
    try:
        record = Record()
        record.startRecording()
        time.sleep(10)
        record.stopRecording()

    except Exception as e:
        print(f"An error occurred: {e}")
