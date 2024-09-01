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
from globals import STATE
from config import cf


responces_past = {
    "mood": 'I thought earlier that you looked %s.  What''s happening? ',
    "evesdrop": 'I heard you say "%s" earlier.  What were you talking about? '
}
  
responces_now = {
    "mood": 'You look %s.  What''s happening? ',
    "evesdrop": 'Did you just say %s? '
}

class AI_Dude(AI):

    name = "Dude"

    def __init__(self):
        AI.__init__(self)
        print("Welcome to D.U.D.E!")
        return

    # respond to the users statement
    def respond(self, user_input):

        cp = ["Don't have a good day, have a GREAT day!", "OFFICER JOHNNY!!", "Playtime's over.",
                "There are three things I love in life.  Kickin' ass, TBD, third thing here.", "intelligent responce",
                "Harder laughter",  "Friendly gesture", "Encouraging comment", "CATCHPHRASE", "Data not found", "Insert reply here", 
                 "Maximum Effort", "It's just a sweet sweet fantasy baby", "You seem adjective."
            ]


        parent_resp = AI.respond(self, user_input)
        if parent_resp:
            if parent_resp[0] == '#':  # its a picture
                user_input = user_input[1:]
            if parent_resp[0] == '!':  # its an instruction
                user_input = user_input[1:]
            else:
                return parent_resp

        # number guess
        # joke
        # google results
        # weather 
        return cp[random.randint(0, len(cp)-1)]

    #ON Startup
    def Hello(self):
        return f"CATCHPHRASE"

    def Intruder(self):
        return "INTRUDER!! Playtime's Over!  Intimidating flexing"

    # On Wake State
    def WakeMessage(self):
        resp = f"You rang {cf.g('USERNAMEP')}?"
        return resp
    
    # From Sleep State
    def Greet(self):
        resp = f"I just woke up! Good {AI.TimeOfDay(self)} {cf.g('USERNAMEP')}."
        resp += f"It's been {AI.PrettyDuration(self, datetime.now() - self.last_user_interaction)} since we talked last."
        return resp
    
    def Think(self):      
        return AI.Think(self)
        
    def InitiateConvo(self):
        print("initialte convo")
        ret = self.ProcessMessages()
        if not ret:
            ret = "so whats new?"
        return ret

    def ProcessMessages(self):
       ret = ""
       for m in  self.messages.GetMessages():
            message = m[1]
            ret += responces_past[m[0]] % message
       return ret

    def Close(self):
       AI.Close(self)
       return

if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')
 
    ai = AI_Dude()
    print(ai.InitiateConvo())
    print(ai.ProcessMessages())

    ai.messages.SetMessage('mood', 'sad', datetime.now())
    ai.messages.SetMessage('evesdrop', 'i like pie', datetime.now())
    ai.messages.SetMessage('mood', 'angry', datetime.now())
    print(ai.ProcessMessages())







    
#    ai.say("Hello!  ")
#    imp = ai.listen()
#    ai.say(f'You said {imp}')

#    print(f"Can I see you? {ai.LookForUser()}")
#    print(f'Evesdrop: {ai.Interact(2)}') # set evesdrop
#    print(f'Return Message? {ai.Interact(2)}') # set evesdrop
#    print(f'Evesdrop: {ai.Interact(2)}') # set evesdrop
#    print(f'Init Convo: {ai.Interact(3)}') # set evesdrop



