import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
from AI_class import AI
import random

# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from error_handling import *
from globals import STATE, HasInternet, GetHostname
from config import cf

class AI_Offline(AI):

    name = "Offline"
    training = True
    def __init__(self):
        AI.__init__(self)
        LogInfo("No Internet.  Starting offline.")
        return

    # respond to the users statement
    def respond(self, user_input):
        return ""

    #ON Startup
    def Hello(self):
        return ""

    def Close(self):
       AI.Close(self)
       return

    # override listen functionality to block listening altogether.  In case user chooses to not have cat greet on boop.
    def listen(self, beQuiet=False):
        STATE.ChangeState('SleepState')
        self.face.off()
        return ""

    def say(self, txt="", asyn=False):
        self.face.thinking()
        if HasInternet():
            STATE.data = []
            STATE.data.append(f"self.SwitchAI('{cf.g('AI_ENGINE')}')")
            STATE.ChangeState('Hello')
            STATE.ChangeState('EvalCode')  # will revert to previous state (Wake)
            self.face.thinking()
            return AI.say(self, "I have internet again!")
        else:
            self.mouth.PlaySound(cf.g('ERROR_FILE'))
#            self.mouth.PlaySound(cf.g('WIFI_FILE'))
            self.face.off()
            return False

if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Active')
 
    ai = AI_Offline()
    inp = ""
    while inp != "quit":
        inp = input()
        print("AI: "+ ai.respond(inp))
  





    
#    ai.say("Hello!  ") imp = ai.listen() ai.say(f'You said {imp}')

#    print(f"Can I see you? {ai.LookForUser()}")
#    print(f'Evesdrop: {ai.Interact(2)}') # set evesdrop
#    print(f'Return Message? {ai.Interact(2)}') # set evesdrop
#    print(f'Evesdrop: {ai.Interact(2)}') # set evesdrop
#    print(f'Init Convo: {ai.Interact(3)}') # set evesdrop



