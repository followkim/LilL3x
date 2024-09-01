import traceback
import sys

def RaiseError(e):
    print (e)
    DumpStack()
    return False

def DumpStack():
    traceback.print_stack()
