import traceback
import sys
import os
from datetime import datetime
import shutil
import time 
import threading

err_level = {
    1: "Conversation",
    2: "Warnings",
    3: "Info Messages",
    4: "Debug Messages"
}

ERROR_LEVEL = 4

log_file_name = ""
log_file_ln = "lill3x.log"
log_file = 0

def InitLogFile():
    try:
        log_file_name = "./log/lill3x"+datetime.now().strftime("%Y%m%d%H%M")+".log"
        logFile = open(log_file_name, "a")
        logFile.write(f"{datetime.now()}\n")
        logFile.close()
        try:
            os.remove(log_file_ln)
        except FileNotFoundError:
            pass
        try:
            os.symlink(log_file_name, log_file_ln)
            print(f"Log File Created: " + log_file_name)
        except Exception as e:
            print(f"Unable to create log file link: {str(e)}")
        logFile = open(log_file_name, "a")

    except Exception as e:
        print(f"Unable to create log file: {str(e)}")

def ShowThreads():
    threads = threading.enumerate()
    numThreads = len(threads)
    LogInfo(f"{numThreads} total threads:")
    for t in threads: LogInfo(f"\t\t{t.name}")

def SetErrorLevel(level):
    global ERROR_LEVEL
    if ERROR_LEVEL != level: 
        Log(f"Log level changed from {err_level[ERROR_LEVEL]} to {err_level[level]}.")
        ERROR_LEVEL = level
    return

def RaiseError(e):
    LogError(e)
    DumpStack()
    return False

def LogFatal(text):
    return RaiseError(text)

def LogError(text):
    Log(text, "ERR:")
    return

def LogConvo(txt):
    if ERROR_LEVEL >= 1:
        Log(txt, "")
    return

def LogWarn(txt):
    if ERROR_LEVEL >= 2:
        Log(txt, "WARN:")
    return

def LogInfo(txt):
    if ERROR_LEVEL >= 3:
        Log(txt, "INFO:")
    return

def LogDebug(txt):
    if ERROR_LEVEL >= 4:
        Log(txt, "DEBUG:")
    return

def Log(text, level=""):
    if ERROR_LEVEL >= 2 or log_file_name == "": print(f"{level} {text}")
    if log_file_name:
        try:
            logFile = open(log_file_name, "a")
            logFile.write(f"{level}{text}\n")
            logFile.close()
        except Exception as e:
            print(f"Error writing to logfile: {str(e)}")
def DumpStack():
    traceback.print_stack()

def CloseLog():
    try:
        os.remove(log_file_ln)
    except FileNotFoundError:
        pass

#   shutil.move(log_file_name, 'log/'+log_file_name+datetime.now().strftime("%Y%m%d%H%M")+".log")

def CleanLogs():
    time_in_secs = time.time() - (30 * 24 * 60 * 60) #30 days -- need a constant here as we can't access cf
    if os.path.exists('./log'):
        for root_folder, folders, files in os.walk('./log'):
            for file in files:
                file_path = os.path.join(root_folder, file)
                if os.path.getctime(file_path) < time_in_secs:
                    os.remove(file_path)

CleanLogs()
