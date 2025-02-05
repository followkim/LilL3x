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
#        self.client = lc.ChatOllama(base_url =self.base_url, model=self.model(), temperature=cf.g('TEMPERATURE'))
        self.client=ollama.Client(host=self.base_url)
        self.memory = self.LoadConvo()
        return

    def ai_respond(self, user_input, canParaphrase=False):  # called from AI_openAI.respond().  Has wrapper to handle convo
        self.face.thinking()
        class_resp = AI.respond(self, user_input)  # will return either a response
        args = {
            'model': self.model(),
            'messages': self.memory,
            'stream': True,
            }

        (user_input, args) = self.HandleResponse(class_resp, user_input, args)
        if not user_input:
            self.face.off()
            return class_resp #hacky - if the class doesn'tt return text then assume that they handled it.

        reply = ""
        LogDebug(str(args['messages'][-1]))
        try:
            if args['stream']: reply = self.reply_async(args)
            else: reply = self.reply_sync(args)
            self.memory.append({"role": "assistant", "content": reply, "id": cf.g('CONVO_ID')},) # overwrite reply

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
        face = self.face
        response = self.client.chat(**args)

#        if args['model']==self.model(vision=True):
        if cf.g('GIVE_PICT_DESC') in str(args['messages'][-1]):
            face=None            # don't allow mouth to control the face
            self.face.looking()  # turn the screen

        for chunk in response:
            m = chunk['message']['content']
            full_reply = full_reply + m
            eos = re.search(r"(^|[^.])(!|\.|\?)( |$)", m)
            if eos:
                reply = reply + m[:(eos.span()[0])+2]
                self.mouth.say(self.StripActions(reply), face=face, asyn=True)
                LogDebug("Async: " + str(chunk))
                reply = m[(eos.span()[0])+2:]
            else: reply = reply + m
        self.mouth.say(self.StripActions(reply), face=face, asyn=False)
        if face: face.off()
        return self.StripActions(full_reply)


    def reply_sync(self, args, shouldStrip=False):
#        ai_msg = self.client.invoke(input=args['messages'], kwargs=args)
#        reply = ai_msg.content
        reply = ""
        response = self.client.chat(**args)
        if response['message']['content']:
            reply = response['message']['content']
        LogDebug("Sync: " + str(response))
        if shouldStrip: return self.StripActions(reply)
        else: return reply

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
#            arg['model'] = self.slow_model
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
        elif user_input[:1] == '#': #picture
            role = "user"
            (user_input, path, url) = user_input[1:].split('#')

            if user_input[0] == "!":
                shouldStream = False
                user_input = user_input[1:]
            else:
                shouldStream = True

            if self.model() != self.model(vision=True):  # we have a vision model  and cf.g('USE_DESCRIPTION') TODO
                # get a description of the picture
                arg['stream']=False
                arg['model']=self.model(vision=True)     # if revert, just add this outside if clause
                self.memory.append({"role": role, "content": cf.g('GET_PICT_DESC'),  "id": cf.g('CONVO_ID'), 'images':[path]})
                arg['messages'] = self.memory
                pictDesc = self.reply_sync(arg)
                arg['model']=self.model() #reset the model
                user_input = f"{user_input}.  {cf.g('GIVE_PICT_DESC')}: {pictDesc}"

            self.memory.append({"role": role, "content": user_input, "id": cf.g('CONVO_ID')},)
            arg['stream'] = shouldStream

        #reply is just text
        else:
            self.memory.append({"role": role, "content": user_input, "id": cf.g('CONVO_ID')},)
            if self.tools:
                arg['tools'] = self.tools

        arg['messages'] = self.memory
        return (user_input, arg)

class AI_Local(AI_ollama):
    name = "Local"
    base_url = "http://localhost:11434"
    api_key = "unused"
    model_key = 'LOCAL_MODEL'
    slow_model_key=model_key
    vision_model_key=model_key

class AI_Corgi(AI_ollama):
    name = "Corgi"
    base_url = cf.g('CORGI_URL')
    api_key = cf.g('CORGI_API_KEY')
    model_key = 'CORGI_MODEL'
    slow_model_key=model_key
    vision_model_key=model_key

class AI_El3ktra(AI_ollama):
    name = "El3ktra"
    base_url = cf.g('EL3KTRA_URL')
    api_key = cf.g('EL3KTRA_API_KEY')
    model_key = 'EL3KTRA_MODEL'
    slow_model_key=model_key
    vision_model_key='EL3KTRA_VISION_MODEL'

#    tools = function_tools

if __name__ == '__main__':
    from face import DummyFace
    global STATE
    STATE.ChangeState('Idle')

    ai = AI_El3ktra()
    ai.face = DummyFace()
#    ai.eyes = Camera()
#    print(ai.respond("lets take my picture?"))
#     ai.Greet()
#    ai.WakeMessage()
#    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_inp  = "hello"
#    print(ai.Hello())
#    print(ai.SumMemory())
#    user_inp = "#this is a picture of me, waht do you think?#temp/capture_0_20240912133342132801.jpg#htttp://http://el3ktra.el3ktra.net/uploads/capture_0_20240911223907988147.jpg"
#    out = ai.respond(user_inp)
#    print(f'AI: {out}')

    while user_inp.lower() not in ("quit", "quit."):

        print(f"{cf.g('USERNAME')}: ", end="")
        user_inp = input(f"{cf.g('USERNAME')}: ")
        out = ai.respond("^" + user_inp)
        print(f'AI: {out}')
        print(ai.memory)
#    ai.Close()
