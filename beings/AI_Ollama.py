import json
import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import openai
import ollama
import langchain_ollama as lc
from AI_class import AI
from AI_Openai import AI_openAI
from time import sleep
# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf
from error_handling import *

function_tools =  [
#    {
#    "type":"function",
#    "function": {
#        "name": "SetEvent",
#        "description": "Return the date and time for an upcoming event.  Call when a user describes a future event, for example when the user says 'Have have a doctors appoint tomarrow'",
#        "parameters": {
#            "type": "object",
#            "properties": {
#                "event_name": {
#                    "type": "string",
#                    "description": "The description of the event.",
#                },
#                "event_date": {
#                    "type": "string",
#                    "description": "The date and (if applicable) the time",
#                },
#            },
#            "required": ["event_name", "event_date"],
#            "additionalProperties": False,
#        }
#     }
#  },
  {
    "type":"function",
    "function": {
        "name": "TakePicture",
        "description": "Take a picture with the attached camera.  Only call when the user indicates they want you to look at something or see where they are.",
        "parameters": {
            "type": "object",
            "properties": {
                "picture_context": {
                    "type": "string",
                    "description": "The description of the picture subject.",
                },
            },
            "required": ["picture_subject"],
            "additionalProperties": False,
        }
     }
  }
]



class AI_ollama(AI_openAI):

    tools = False
    token_mult = 1

    def __init__(self):
        AI.__init__(self) # we don't want to init AI_OpenAI, we just want the functions
#        self.client = lc.ChatOllama(base_url =self.base_url, model=self.model, temperature=cf.g('TEMPERATURE'))
        self.client=ollama.Client(host=self.base_url)

        self.memory = [
            {"role": "system", "content": f"Your name is {cf.g('AINAME')}. {cf.g('BACKSTORY')}"}, 
            {"role": "system", "content": 'Your history with the user: '+cf.g('HISTORY')},
        ]
        LogInfo(f"AI {self.name}, ({self.model}) loaded.")
        return


    def respond(self, user_input, canParaphrase=False):
        self.face.thinking()
        class_resp = AI.respond(self, user_input)  # will return either a response
        args = {
            'model': cf.g(f'{self.name.upper()}_MODEL'),
            'messages': self.memory,
            'stream': True
         #   'temperature': cf.g('TEMPERATURE')
            }
        (user_input, args) = self.HandleResponse(class_resp, user_input, args)
        if not user_input:
            self.face.off()
            return class_resp #hacky

        reply = ""
        response = ""
        
        LogDebug(str(args['messages'][-1]))
        try:
            if args['stream']: reply = self.reply_async(args) 
            else: reply = self.reply_sync(args)
            self.memory.append({"role": "assistant", "content": reply, "id": cf.g('CONVO_ID')},) # overwrite reply
            self.TrainData(user_input, reply)

        except Exception as e:
            reply = f"There was an error talking to Ollama. {str(e)}"
            args['stream'] = False
            self.memory.pop()  #get rid of that bad membry!

        self.face.off()
        if args['stream']: return "" # don't return the reply if streaming, it's already been spoken
        else: return reply
     
    def reply_async(self, args):
        reply = ""
        full_reply = ""
        response = self.client.chat(**args)
#        for chunk in self.client.stream(input=args['messages'], kwargs=args):
        for chunk in response:
            m = chunk['message']['content']
#            m = chunk.content
            full_reply = full_reply + m
            eos = re.search(r"(^|[^.])(!|\.|\?)( |$)", m)
            if eos:
                reply = reply + m[:(eos.span()[0])+2]
                self.mouth.say(self.StripActions(reply), asyn=True)
                LogDebug("Async: " + str(chunk))
                reply = m[(eos.span()[0])+2:]
            else: reply = reply + m
        self.mouth.say(self.StripActions(reply), asyn=False)
        return self.StripActions(full_reply)


    def reply_sync(self, args):
#        ai_msg = self.client.invoke(input=args['messages'], kwargs=args)
#        reply = ai_msg.content
        reply = ""
        response = self.client.chat(**args)
        if response['message']['content']:
            reply = response['message']['content']
        LogDebug("Sync: " + str(response))
        return self.StripActions(reply)

    #NOte: this function alters the memory
    def HandleResponse(self, class_resp, user_input, arg, canParaphrase=False):
#       The parent class handled the input.  
#       Unless told to paraphrase, return
#        max_tokens = 500*self.token_mult
        local_tools = {}
        if class_resp:
            if class_resp == "goodbye": # allow the AI to say goodbye
                user_input =  "I have to go now, goodbye"
            elif canParaphrase and not cf.g('SAVE_TOKENS'):  # something to paraphrase
                user_input = "Paraphrase '"+class_resp+"'"
            elif not class_resp[0].isalpha(): # contains instructions (!, #, @)
                user_input = class_resp
            else:
                return (False, False) ## go with the class responce

#        return "ChatGPT: '"+user_input+"'"  # uncomment to test without using tokens
        role = "user"
        ret_tools = {}
        if user_input[:1] == '>': #text
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": user_input, "id": cf.g('CONVO_ID')},)

        #reply is a command 
        elif user_input[:1] == '!': #command
             role = "user"
#             arg['model'] = self.slow_model
             arg['stream'] = False
             user_input = user_input[1:]
             self.memory.append({"role": role, "content": user_input, "id": cf.g('CONVO_ID')},)
             #max_tokens=100*self.token_mult  #75 words - keep it short for spontanous uttering

        #reply is a memory request 
        elif user_input[:1] == '^': #write memories
             role = "user"
             arg['stream'] = False
             user_input = user_input[1:]
             self.memory.append({"role": role, "content": user_input, "id": cf.g('CONVO_ID')},)
             #max_tokens=1000*self.token_mult

        #reply is a picture
        elif user_input[:1] == '#': #picture-- TODO!!!
             LogDebug(f"Input is pict: {user_input}")
             (x, user_input, path, url) = user_input.split('#')
             arg['model']=cf.g('EL3KTRA_VISION_MODEL')
             self.memory.append({"role": role, "content": user_input,  "id": cf.g('CONVO_ID'), 'images':[path]})

        #reply is just text
        else:
             self.memory.append({"role": role, "content": user_input, "id": cf.g('CONVO_ID')},)
             if self.tools:
                 arg['tools'] = self.tools

        arg['messages'] = self.memory
        return (user_input, arg)

    def Close(self):
       AI.Close(self)
       self.SaveMemories()
       return

class AI_Local(AI_ollama):
    base_url = "http://localhost:11434"
    api_key = "unused"
    model = 'qwen2:0.5b'
    slow_model=model
    name = "Local"

class AI_Corgi(AI_ollama):
    base_url = cf.g('CORGI_URL')
    api_key = cf.g('CORGI_API_KEY')
    model = cf.g('CORGI_MODEL')
    slow_model=model
    name = "Corgi"

class AI_El3ktra(AI_ollama):
#    base_url = cf.g('EL3KTRA_URL')
    base_url = cf.g('EL3KTRA_URL')
    api_key = 'el3ktra'
    model = cf.g('EL3KTRA_MODEL')
    slow_model=model
    name = "El3ktra"
#    tools = function_tools

if __name__ == '__main__':
    from camera_tools import Camera
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
        def say(self, txt, asyn=False):
             print(txt)
        def IsBusy(self):
             return False
    ai = AI_El3ktra()
    ai.leds = LEDS()
    ai.face = LEDS()
#    ai.eyes = Camera()
    ai.mouth = LEDS()
#    print(ai.respond("lets take my picture?"))
#     ai.Greet()
#    ai.WakeMessage()
#    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_inp  = "hello"
    print(ai.Hello())

#    user_inp = "#this is a picture of me, waht do you think?#temp/capture_0_20240912133342132801.jpg#htttp://http://el3ktra.el3ktra.net/uploads/capture_0_20240911223907988147.jpg"
#    out = ai.respond(user_inp)
#    print(f'AI: {out}')

    while user_inp != "quit":

        print(f"{cf.g('USERNAME')}: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')

#    ai.Close()
