from datetime import datetime, timedelta
from state import State, MicStatus
from time import sleep

MIC_STATE = MicStatus()
STATE = State()

# A version of sleep that will break out if a function return changes (or STATE changes).   Avoids long period of uninterruptable sleep.
def SleepOn(secs, varf=STATE.GetState, step=0.5, watchState=True):
    if watchState: thisState = STATE.GetState()
    var = varf()  # starting condition
    sleep_for = min(step, max(secs,step))
    target_time = datetime.now() + timedelta(seconds=secs)

    while var==varf() and (secs<0 or datetime.now() < target_time) and (not watchState or STATE.CheckState(thisState)):
        sleep(sleep_for)

if __name__ == '__main__':
    def q2q():
         return input("q2q: ")=='q'
    SleepOn(10, q2q)  # shoudl quit after 10 sec (input is blocking)
