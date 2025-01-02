import traceback
import sys
import os
import re
from datetime import datetime
import time
import threading

err_level = {
    0: "Errors Only",
    1: "Conversation",
    2: "Warnings",
    3: "Info Messages",
    4: "Debug Messages"
}

ERROR_LEVEL = 4

log_file_name = ""
log_file_ln = "lill3x.log"

def InitLogFile():
    global log_file_name
    global log_file_ln
    try:
        log_file_name = "./log/lill3x_"+datetime.now().strftime("%Y%m%d_%H")+".log"
        logFile = open(log_file_name, "a")
        logFile.write(Color(f"\n\n\n\n********** LOG STARTED **********\n", 'cyan'))
        logFile.write(Color(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", 'cyan'))
        logFile.close()
        print(f"Log File Created: " + log_file_name)
        LnFile()
    except Exception as e:
        print(f"Unable to create log file: {str(e)}")

def LnFile():
    global log_file_name
    global log_file_ln

    if log_file_name == "": return False

    #Check the link file
    try:
        if os.path.exists(log_file_ln) and os.readlink(log_file_ln) != log_file_name:
            os.remove(log_file_ln)
    except: pass
    try:
        if not os.path.exists(log_file_ln):
            os.symlink(log_file_name, log_file_ln)
            if os.path.exists(log_file_ln):
                print("Log Link Created: " + log_file_ln)
    except Exception as e:
        print(f"Unable to create log file link: {str(e)}")
    return os.path.exists(log_file_ln) and os.readlink(log_file_ln) != log_file_name


def ShowThreads():
    threads = threading.enumerate()
    numThreads = len(threads)
    for t in threads:
        LogInfo(f"\t\t{t.name}")
        if not re.search("^LilL3x", t.name): numThreads = numThreads - 1
    LogInfo(f"{len(threads)} total threads, {numThreads} LilL3x threads.")
    return numThreads+1   # add main Thread

def SetErrorLevel(level):
    global ERROR_LEVEL
    if ERROR_LEVEL != level: 
        LogInfo(f"Log level changed from {err_level[ERROR_LEVEL]} to {err_level[level]}.")
        ERROR_LEVEL = level
    return

def RaiseError(e):
    LogError(e)
    DumpStack()
    return False

def LogFatal(txt):
    return RaiseError(txt)

def LogError(txt):
    Log(txt, Color("ERR:\t", 'red'))
    return

def LogConvo(txt):
    if ERROR_LEVEL >= 1:
        ta = txt.split(":", 1)
        Log(ta[1], Color(ta[0]+": ", 'purple'))
    return

def LogWarn(txt):
    if ERROR_LEVEL >= 2:
        Log(txt, Color("WARN:\t", 'yellow'))
    return

def LogInfo(txt):
    if ERROR_LEVEL >= 3:
        Log(txt, Color("INFO:\t", 'blue'))
    return

def LogDebug(txt):
    if ERROR_LEVEL >= 4:
        Log(txt, Color("DEBUG:\t", 'green'))
    return

def Log(text, level=""):
    global log_file_name
    global log_file_ln

    if log_file_name == "": print(f"{level}{text}")
    if log_file_name:
        try:
            logFile = open(log_file_name, "a")
            logFile.write(f"{level}{text}\n")
            logFile.close()
        except Exception as e:
            print(f"Error writing to logfile: {str(e)}")
        LnFile()

def Color(text, color_code):
    colors = {
        'red': 31,
        'green':32,
        'yellow': 33,
        'blue': 34,
        'purple': 35,
        'cyan': 36
    }
    return f"\033[{colors[color_code]}m{text}\033[0m"

def DumpStack():
    if log_file_name:
        try:
            logFile = open(log_file_name, "a")
            traceback.print_stack(file=logFile)
            logFile.close()
        except Exception as e:
            print(f"Error writing to logfile: {str(e)}")
    else: traceback.print_stack()

def CloseLog():
    Log(Color(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'cyan'))
    Log(Color(f"********** LOG ENDED **********\n\n\n\n", 'cyan'))

def CleanLogs():
    time_in_secs = time.time() - (30 * 24 * 60 * 60) #30 days -- need a constant here as we can't access cf
    if os.path.exists('./log'):
        for root_folder, folders, files in os.walk('./log'):
            for file in files:
                file_path = os.path.join(root_folder, file)
                if os.path.getctime(file_path) < time_in_secs:
                    os.remove(file_path)

CleanLogs()

if __name__ == '__main__':

    InitLogFile()
    Log("test")
    SetErrorLevel(4)
    s = ""
    while s != 'quit':
        s=input("input: ")
        LogInfo(s)
    RaiseError(s)
    CloseLog()
