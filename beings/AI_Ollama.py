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

class AI_ollama(AI_openAI):
    api_key = ""
    tools = False
    token_mult = 1
    auth_header = None

    def __init__(self):
        AI.__init__(self) # we don't want to init AI_OpenAI, we just want the functions

#        self.client = lc.ChatOllama(base_url =self.base_url, model=self.model(), temperature=cf.g('TEMPERATURE'), auth=(cf.g('USEREMAIL'), self.api_key))
        self.client=ollama.Client(host=self.base_url, auth=(cf.g('USEREMAIL'), self.api_key))
        self.memory = self.LoadConvo()
        return

    def ai_respond(self, user_input, canParaphrase=False):  # called from AI_openAI.respond().  Has wrapper to handle convo
        self.face.thinking()
        class_resp = AI.respond(self, user_input)  # will return either a response
        if class_resp in ( "!", ""): return "" 
        args = {'model': self.model(), 'stream': True}

        (user_input, args) = self.HandleResponse(class_resp, user_input, args)
        if not user_input:
            self.face.off()
            return class_resp #hacky - if the class doesn'tt return text then assume that they handled it.

        reply = ""
        LogDebug(str(args['messages'][-1]))
        try:
            if args['stream']: reply = self.reply_async(args)
            else: reply = self.reply_sync(args)
            self.memory.append({"role": "assistant", "content": reply}) # overwrite reply

        except Exception as e:
            LogError(f"There was an error talking to Ollama. {str(e)}")
            reply = f"I had a slight glitch, give it a second and try again."
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
            face=False       # don't allow mouth to control the face
            self.face.looking()  # turn the screen
            self.face.leds.thinking()
        for chunk in response: #self.client.stream(self.GetMemory()):
            m = chunk['message']['content']
#            m = chunk.content LC
            full_reply = full_reply + m
            eos = re.search(r"(^|[^.])(!|\.|\?)( |$)", m)
            if eos:
                reply = reply + m[:(eos.span()[0])+2]
                if not face: self.face.leds.talking()
                self.mouth.say(self.StripActions(reply), face=face, asyn=True)
                LogDebug("Async: " + str(chunk))
                reply = m[(eos.span()[0])+2:]
                if not face: self.face.leds.thinking()
            else: reply = reply + m
        self.mouth.say(self.StripActions(reply), face=self.face, asyn=False)
        self.face.off()
        return self.StripActions(full_reply)


    def reply_sync(self, args, shouldStrip=False):
#        ai_msg = self.client.invoke(input=args['messages'], kwargs=args)
#        reply = ai_msg.content
        reply = ""
        
        response = self.client.chat(**args)
#        response = self.client.invoke(self.GetMemory())
#        if response.content: LC
#            reply = response.content
        if response['message']['content']:
            reply = response['message']['content']

        LogDebug("Sync: " + str(response))
        if shouldStrip: return self.StripActions(reply)
        else: return reply

    #NOte: this function alters the memory
    def HandleResponse(self, class_resp, user_input, arg):
#       The parent class handled the input.  
#       Unless told to paraphrase, return
#        max_tokens = 500*self.token_mult
        local_tools = {}
        if class_resp:
            if not class_resp[0].isalpha(): # contains instructions (!, #, @)
                user_input = class_resp
            else:
                return (False, False) ## go with the class responce
            
#        return "ChatGPT: '"+user_input+"'"  # uncomment to test without using tokens
        role = "user"
        ret_tools = {}
        if user_input[:1] == '>': #text
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": user_input})

        elif user_input[:1] == '~': #paraphrase
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": f"Paraphrase this: {user_input}"})

        #reply is a command
        elif user_input[:1] == '!': #command
            role = "user"
#            arg['model'] = self.slow_model
            arg['stream'] = False
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": user_input})
            #max_tokens=100*self.token_mult  #75 words - keep it short for spontanous uttering

        #reply is a memory request 
        elif user_input[:1] == '^': #write memories
            role = "user"
            arg['stream'] = False
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": user_input})
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
                arg['messages'] = [{"role": role, "content": cf.g('GET_PICT_DESC'),  'images':[path]}]
                pictDesc = self.reply_sync(arg)

                arg['model']=self.model() #reset the model
                user_input = f"{user_input}.  {cf.g('GIVE_PICT_DESC')}: {pictDesc}"

            self.memory.append({"role": role, "content": user_input})
            arg['stream'] = shouldStream

        #reply is just text
        else:
            self.memory.append({"role": role, "content": user_input})
            if self.tools:
                arg['tools'] = self.tools

        arg['messages'] = self.GetMemory()
        return (user_input, arg)

    def SumMemory(self, memory=False):
        if not memory: memory = self.memory[2:]  # skip system instructions when using own memory

        memory.append({"role": "user", "content": "Summarize the above {len(memory)} items, focusing on facts (namely about the user), upcoming events, current and future projects, and frequent topics.  Be detailed and comprhensive.  This will be saved to reshresh memory later."})

        args = {
            'model': self.model(),
            'messages': memory
        }
        sum = self.reply_sync(args, False) # don't strip response
        return sum

class AI_Adhoc(AI_ollama):
    name = "AdHoc"
    base_url = cf.g('ADHOC_URL')
    api_key = cf.g('ADHOC_API_KEY')
    model_key = 'ADHOC_MODEL'
    slow_model_key='ADHOC_MODEL_SLOW'
    vision_model_key='ADHOC_VISION_MODEL'

class AI_Corgi(AI_ollama):
    name = "Corgi"
    base_url = cf.g('CORGI_URL')
    api_key = cf.g('CORGI_API_KEY')
    model_key = 'CORGI_MODEL'
    slow_model_key=model_key
    vision_model_key='CORGI_VISION_MODEL'

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
    class mouth:
        def say(self, txt, face=None, asyn=False):
            print(txt)

    ai = AI_El3ktra()
    ai.face = DummyFace()
    ai.mouth = mouth()
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
        out = ai.respond(user_inp)
        print(f'AI: {out}')
#    ai.Close()
