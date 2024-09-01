import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import requests
import json
import Bard 
from AI_class import AI
import bardapi
# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf


bard_api = cf.g('BARD_API')

responces_past = {
     "mood": 'earlier you saw the user looked %s. Ask them about that. ',
    "evesdrop": 'you heard the user say "%s" earlier. ask a follow up question'
}
  
responces_now = {
    "mood": 'earlier you saw the user looked %s. Ask them about that. ',
    "evesdrop": 'you heard the user say "%s" earlier. ask a follow up question'
}


class AI_Bard(AI):

    Barddata = []  # called messges but I already used that name.  I should replace my messages
    client = 0

    def __init__(self):
        AI.__init__(self)
        return

    def respond(self, user_input, canParaphrase=False):
        class_resp = AI.respond(self, user_input)  # will return either a response
#       The parent class handled the input.  Just paraphrase and give back to user:
        if class_resp:
            if class_resp == "Goodbye":
                user_input =  "I have to go now, goodbye"
            elif canParaphrase:
                user_input = "Paraphrase '"+class_resp+"'"
            else:
                return class_resp
#        return "Bard: '"+user_input+"'"  # uncomment to test without using tokens

        print(cf.g('BARD_API'))
        bard_URL = "https://bard.googleapis.com/v1/generate"
        response = requests.post(bard_URL, headers={"Authorization": "Bearer " + cf.g('BARD_API')}, json={"query": user_input})
        print(str(response))

        data = json.loads(response.content)
        print(str(data))
        return data["text"]

    #ON Startup
    def Hello(self):
        return f"Hello, my name is {cf.g('USERNAMEP')}."
#             return cf.g('USERNAMEP')+" just arrivted after "+AI.PrettyDuration(self, datetime.now() - self.last_interaction) +", greet them.#        else:
#              return self.respond("Hello!")

    # On Wake State return greeting
    def WakeMessage(self):
        resp = "Hello, are you there?"
        return self.respond(resp)
        
    
    # From Sleep State return greeting
    def Greet(self):
          resp = "I'm back"
#         resp = cf.g('USERNAMEP')+" just returned after "+AI.PrettyDuration(self, datetime.now() - self.last_interaction) +", greet them."

 #       resp = AI.Greet(self)
             # and you haven't seen the user for  " + AI.PrettyDuration(datetime.now() - self.last_interaction) + ".  Greet them."
          return self.respond(resp)
    
    def Think(self):      
        return AI.Think(self)
        
    def InitiateConvo(self):
        print("initialte convo")
        ret = self.ProcessMessages()
        if not ret:
            ret = f"Ask me how my {AI.TimeOfDay(self)} is going."
#        return ret
        return self.respond(ret)

    # called from init convo -- do not process (InitCOnvo will process)
    def ProcessMessages(self):
       ret = ""
       for m in  self.messages.GetMessages():
            message = m[1]
#            ret = responces_past[m[0]] % message
       return ret


    def Close(self):
       AI.Close(self)

       #write the conversattion to file
       print(self.Barddata)

#       file = open(cf.g(['Bard_HISTORY']), "a+")
#       file.write(str(self.Barddata))
#       file.close()
 
       return


    def get_emotion(self):
        return self.respond("in one word does user feel happy, sad, afraid or angry?")

if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')
     
    ai = AI_Bard()
    ai.Greet()
    ai.WakeMessage()
    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_imp  = "hello"
    while user_imp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')
   
