from socket import gethostname
from datetime import datetime, timedelta
from state import State, MicStatus
from time import sleep
from subprocess import check_output

MIC_STATE = MicStatus()
STATE = State()

# A version of sleep that will break out if a function return changes (or STATE changes).   Avoids long period of uninterruptable sleep.
def SleepOn(secs=-1, varf=STATE.GetState, step=0.5, watchState=True, wakeOn=None):

    haveWake = wakeOn!=None

    if watchState:
        thisState = STATE.GetState()
        if STATE.ShouldWake(): return

    # starting condition
    var = varf()
    sleep_for = min(step, max(secs,step))
    target_time = datetime.now() + timedelta(seconds=secs)

    while ((haveWake and varf()!=wakeOn) or (not haveWake and var==varf())) and (secs<0 or datetime.now() < target_time) and (not watchState or STATE.CheckState(thisState)):
        sleep(sleep_for)


def GetIP():
    try:
        ips = check_output(['hostname', '--all-ip-addresses'])
        return ips.split()[0].decode()
    except Exception as e:
        print(e.args)
        return False

def GetHostname():
        return gethostname()

if __name__ == '__main__':
    def q2q():
         return input("q2q: ")=='q'

    inp = input("WakeOn: (true/false)")
    if inp[0]=="t": SleepOn(10, q2q, wakeOn=True)
    elif inp[0]=="f": SleepOn(-1, q2q, wakeOn=False)
    else: SleepOn(10, q2q)  # shoudl quit after 10 sec (input is blocking)

    print(GetIP())
    print(GetHostname())
