from datetime import datetime, timedelta
from time import sleep
import traceback
from error_handling import *
STATE = 0
MIC_STATUS = 0

class State:
    current = ''
    last_dt = ''
    data = ''
    cx=-1
    cy=-1

    def __init__(self):
        self.current = 'Hello'
        self.last_dt = datetime.now()

    def GetState(self):
        return self.current
    
    def CheckState(self, checkState):
        return self.current == checkState

    def ChangeState(self, new_state):
        if self.current == 'Wake' and new_state != 'Active':
            return self.current             # can only move to Active from Wake-- don't everwrite Wake
        elif self.current not in ('Quit'):  # can't change out of quit state
            LogInfo(f"State changed: from {self.current} to {new_state} after being idle for {self.StateDuration()} secs")
            self.current = new_state
            self.last_dt = datetime.now()
        return self.current

    def StateDuration(self):
        return (datetime.now()-self.last_dt).seconds

    def ResetStateDuration(self):
        self.last_dt = datetime.now()
        return self.last_dt

    def ShouldWake(self):
        return self.current == "Wake"

    def IsInteractive(self):
        return self.current in ('Hello', 'Wake', 'Active')

    def IsInactive(self):
        return self.current not in ('ActiveIdle', 'Surveil') and not self.IsInteractive()

class MicStatus:
    def __init__(self):
        self.mic_free = True
        self.request_mic = False

    def TakeMic(self, timeout=3):
        self.request_mic = True
        if timeout: ud = datetime.now() + timedelta(seconds=timeout)
        while not self.mic_free:          
            self.request_mic = True    ## ask WW for the mic 
            if timeout and datetime.now() > ud:
                LogError("Unable to get mic (timeout)")
                return False
            continue
        self.mic_free = False
        self.request_mic = False
        return True

    def ReturnMic(self):
        self.request_mic = False
        self.mic_free = True
        return True

    def MicRequested(self):
        return self.request_mic

    def MicFree(self):
        return self.mic_free

    def WaitMic(self):
        while not self.mic_free:
            sleep(0.5)
        return self.mic_free

    def CanUse(self):
        return (not self.request_mic and self.mic_free)
        return True
    

if __name__ == '__main__':

    s = State()
    s.ChangeState('Active')
