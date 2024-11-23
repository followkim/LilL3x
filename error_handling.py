import traceback
import sys
from datetime import datetime
import shutil

ERROR_LEVEL = 6
log_file_name = "lill3x.log"

def SetErrorLevel(level):
    global ERROR_LEVEL
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
    print(f"{level}{text}")
    logFile = open(log_file_name, "a")
    logFile.write(f"{level}{text}\n")
    logFile.close()

def DumpStack():
    traceback.print_stack()

def CloseLog():
    shutil.move(log_file_name, 'log/'+log_file_name+datetime.now().strftime("%Y%m%d%H%M")+".log")
