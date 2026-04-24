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
from globals import STATE
from config import cf

class AI_Dude(AI):

    name = "D.U.D.E."
    training = True
    def __init__(self):
        AI.__init__(self)
        LogInfo("Welcome to D.U.D.E!")
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
            if parent_resp[0] == '~':  # its an paraphrase
                user_input = user_input[1:]
            else:
                return parent_resp

        # number guess
        # joke
        # google results
        # weather 
        reply= cp[random.randint(0, len(cp)-1)]
        self.TrainData(user_input, reply)
        return reply

    #ON Startup
    def Hello(self):
        return f"CATCHPHRASE"

    def Intruder(self):
        return "INTRUDER!! Playtime's Over!  Intimidating flexing"

    def Close(self):
       AI.Close(self)
       return

if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')
 
    ai = AI_Dude()
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



