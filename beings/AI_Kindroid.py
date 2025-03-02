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

# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

class AI_Kindroid(AI):

    bearer_token = ''
    has_auth = False
    name = "Kindroid"
    training = True

    def __init__(self):
        AI.__init__(self)
        LogInfo("AI Kindroid Loaded") 
        return

    def respond(self, user_input, canParaphrase=True):
        img_url = None
        img_desc = None
        stream = True
        reply = ""
        start= datetime.now()
        try:
            class_resp = AI.respond(self, user_input)  # will return either a response
            # If class_resp not False, the parent class handled the input.
            if class_resp:
                if class_resp == "!": return ""
                elif class_resp[0] == '#':  # its a picture
                    user_input = class_resp[1:]
                elif class_resp[0] == '~':  # paraphrase
                    return class_resp[1:]
                elif user_input[0] == '!':  # its an instruction
                    stream=False
                    user_input = user_input[1:]
                else:
                    return class_resp  # everythign else just read as is
        except Exception as e:
             LogError(f"Kindriod: Exception handing class response.  User_input:{user_input}, Error: {e.args}" )

        # send the request
        self.face.thinking()
        try:

            chat_headers = {
                'accept': 'application/json, text/plain, */*',
                'authorization': 'Bearer '+ cf.g('KINDROID_API'),
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36'
            }
            chat_data = {
                'ai_id': cf.g('KINDROID_GMPID'),
                'message': user_input #,
#                'stream': stream #, 
                #'image_url': img_url,'image_description':img_desc, 'internet_response': None,'link_url': None,'link_description': None
            }

            responce = requests.post(cf.g('KINDROID_URL'), headers=chat_headers,  data=json.dumps(chat_data), stream=stream)
            if stream:
                p_reply = ""
                reply = ""
                eos = False
                LogDebug("sreaming resp")
                for chunk in responce.iter_content():
                    m = chunk.decode('utf-8')
                    reply = m
                    eos = re.search(r"(^|[^.])(!|\.|\?)( |$)", m)
                    if eos:
                        p_reply = p_reply + m[:(eos.span()[0])+2]
                        self.mouth.say(self.StripActions(p_reply), face=self.face, asyn=True)
                        p_reply = m[(eos.span()[0])+2:]
                    else: p_reply = p_reply + m
                self.mouth.say(self.StripActions(p_reply), face=self.face, asyn=False)  # when done say what is left
                self.TrainData(user_input, reply)
                reply = ""

            else:
                LogDebug("sync resp")
                LogDebug(responce)
                if responce.status_code == 200:
                    reply = responce.text
                    self.TrainData(user_input, reply)
                else:
                    reply = "Sorry, I can't seem to reach the internet.  I got error {responce}"
                    LogError(f"Error {responce} talking to Kindroid")
        # otherise, there was an error
        except Exception as e:
            reply = "Sorry, I can't seem to reach the internet.  I got an error trying to talk to Kindroid."
            LogError(f"Exception talking to Kindroid: {e.args}" )

        self.face.off()
        LogInfo(f"Completed request in {(datetime.now()-start).total_seconds()}s")
        return reply

    def Close(self):
       AI.Close(self)
       return


if __name__ == '__main__':
    from speech_tools import DummySpeech
    from face import DummyFace

    global STATE
    STATE.ChangeState('Idle')

    ai = AI_Kindroid()
    ai.face = DummyFace()
    ai.mouth = DummySpeech()
#    ai.Greet()
#    ai.WakeMessage()
#    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_inp  = "hello"
    while user_inp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')
