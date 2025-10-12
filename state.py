from datetime import datetime, timedelta
from time import sleep
import traceback
from error_handling import *
from gpiozero import CPUTemperature
import psutil
from subprocess import check_output

STATE = 0
MIC_STATUS = 0

class State:
    current = ''
    last_dt = ''
    last_state = ''
    data = ''
    cx=0
    cy=0
    last_hw_dt = ''
    temp= 0
    cpu = 0
    volume = 2000

    def __init__(self):
        self.current = 'Hello'
        self.last_dt = datetime.now()
        self.last_hw_dt = datetime.now()

    def HWState(self, debug=False, waitTime=10):
        if (datetime.now()-self.last_hw_dt).total_seconds() > waitTime:
            self.temp = round(CPUTemperature().temperature)
            if debug: self.cpu = round(psutil.cpu_percent())
            self.last_hw_dt = datetime.now()

    def GetState(self):
        return self.current
    
    def CheckState(self, checkState):
        return self.current == checkState

    def ChangeState(self, new_state):
        if new_state == self.current: return self.current  # don't do anything if asked to Change State to current state
        if self.current == 'EvalCode' and new_state != self.last_state:
            LogInfo(f"State: tried to change from {self.current} to {new_state}, saving for later.")
            self.last_state = new_state

        elif self.current == 'Wake' and new_state != 'Active' and new_state != 'Quit':
            LogWarn(f"State: tried to change from {self.current} to {new_state}, not allowed.")
            return self.current             # can only move to Active from Wake-- don't everwrite Wake

        elif not self.ShouldQuit():          # can't change out of quit state
            if self.StateDuration()<60: LogInfo(f"State changed: from {self.current} to {new_state} after being in state for {self.StateDuration()} secs")
            elif self.StateDuration()<60*60: LogInfo(f"State changed: from {self.current} to {new_state} after being in state for {round(self.StateDuration()/60)} minutes")
            else: LogInfo(f"State changed: from {self.current} to {new_state} after being in state for {round(self.StateDuration()/3600)} hours")
            self.last_state = self.current
            self.current = new_state
            self.last_dt = datetime.now()
        else: LogWarn(f"State: tried to change from {self.current} to {new_state}, not allowed.")
        return self.current

    def RevertState(self):
        return self.ChangeState(self.last_state)

    def RevertWake(self):
        if (self.current == 'Wake'):
            if self.last_state in ('Wake', 'Active'): self.ChangeState('Active')
            else:
                self.last_dt = datetime.now()
                LogInfo(f"RevertWake: State changed: from {self.current} to {self.last_state} after being idle for {self.StateDuration()} secs")
                self.current = self.last_state

    def StateDuration(self):
        return (datetime.now()-self.last_dt).seconds

    def ResetStateDuration(self):
        self.last_dt = datetime.now()
        return self.last_dt

    def ShouldWake(self):
        return self.current in ("Wake", "EvalCode") or self.ShouldQuit()

    def ShouldQuit(self):
        return self.current in ('Quit', 'Reboot', 'Restart')

    def IsSleeping(self):
        return self.CheckState('SleepState')

    def IsInteractive(self):
        return self.current in ('Hello', 'Wake', 'Active')

    def IsInactive(self):
        return self.current not in ('ActiveIdle', 'Surveil') and not self.IsInteractive() and not self.ShouldQuit()

    def GetIPAddress(self):
        try:
            ips = check_output(['hostname', '--all-ip-addresses'])
            return ips.split()[0].decode()
        except Exception as e:
            LogError(f"GetIpAddress returned error {e.args}")
            return ""

    def GetVolume(self):
        return self.volume


if __name__ == '__main__':

    s = State()
    s.ChangeState('Active')
    print(s.GetIPAddress())
    s.ChangeState('Wake')
    s.RevertWake()
