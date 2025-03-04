import urllib.request
import json
from urllib.error import HTTPError

import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import openai
from AI_class import AI
from error_handling import *
import requests
import json
# import parent modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config import cf

# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

class AI_Nomi(AI):

    bearer_token = ''
    has_auth = False
    name = "Nomi"
    training = True

    def __init__(self):
        AI.__init__(self)
        self.Auth()
        LogInfo("AI Nomi Loaded") 
        return

    def Auth(self):
        self.auth = False
        if cf.g('NOMI_API'):
            self.has_auth = True
        return self.auth

    def respond(self, user_input, canParaphrase=True):
        img_url = None
        img_desc = None
        reply = ""
        class_resp = AI.respond(self, user_input)  # will return either a response
#       The parent class handled the input.
        if class_resp:
            if class_resp == "Goodbye":
                user_input =  "I have to go now, goodbye"
            if user_input[0] == '#':  # its a picture
                user_input = user_input[1]
            if user_input[0] == '!':  # its an instruction
                user_input = user_input[1:]
            if user_input[0] == '@':  # its a link
                user_input = user_input[1:]
            else:
                return class_resp  # everythign else just read as is

        chat_url = cf.g('NOMI_URL').format(cf.g("NOMI_ID"))
        chat_data = {
            'messageTxt': user_input
        }
#        chat_data = json.dumps({"messageText": user_input}).encode("utf-8")
        headers={
            "Authorization": cf.g('NOMI_API'),
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(url=chat_url, method="POST", data=json.dumps({"messageText": user_input}).encode("utf-8"), headers=headers)
        


        # send the request
        self.face.thinking()
        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode())
                reply = response_data['replyMessage']['text']
                self.TrainData(user_input, reply)
        except HTTPError as e:
                error_data = json.loads(e.read().decode())
                LogError(f"Nomi HTTPError: {error_data}")
        except Exception as e:
            LogError(f"Nomi POST Error: {e}")

        self.face.off()
        return reply

    def Close(self):
       AI.Close(self)

 
       return


if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')

    class LEDS:
        def __init__(self):
             return
        def thinking(self):
             return
        def talking(self):
             return
        def off(self):
             return
    from face import DummyFace
    ai = AI_Nomi()
    ai.face = DummyFace()
#    ai.Greet()
#    ai.WakeMessage()
#    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_imp  = "hello"
    while user_imp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')
