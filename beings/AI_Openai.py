import json
import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import openai
import llamaapi
from AI_class import AI

# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

function_tools =  [
    {
    "type":"function",
    "function": {
        "name": "SetEvent",
        "description": "Return the date and time for an upcoming event.  Call when a user describes a future event, for example when the user says 'Have have a doctors appoint tomarrow'",
        "parameters": {
            "type": "object",
            "properties": {
                "event_name": {
                    "type": "string",
                    "description": "The description of the event.",
                },
                "event_date": {
                    "type": "string",
                    "description": "The date and (if applicable) the time",
                },
            },
            "required": ["event_name", "event_date"],
            "additionalProperties": False,
        }
     }
  },
  {
    "type":"function",
    "function": {
        "name": "TakePicture",
        "description": "Take a picture with the attached camera.  Call when the user indicates they want you to look at something or see where they are.",
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



class AI_OpenAI(AI):
    base_url = ""
    api_key = ""
    model = ''
    slow_model=model
    name = ""
    token_mult = 1
    tools = False

    def __init__(self):
        AI.__init__(self)
        if self.base_url == "":
            self.client = openai.Client(api_key=self.api_key,)
        else:
            self.client = openai.Client(api_key=self.api_key,base_url=self.base_url)
        self.memory = [ 
            {"role": "system", "content": f"You name is {cf.g('AINAME')}. {cf.g('BACKSTORY')}"}, 
            {"role": "system", "content": 'Your history with the user: '+cf.g('HISTORY')},
        ]

        return

    def respond(self, user_input, canParaphrase=False):
        this_model = self.model
        class_resp = AI.respond(self, user_input)  # will return either a response
        (user_input, max_tokens, tools) = self.HandleResponse(class_resp, user_input)
        if not user_input:
            return class_resp #hacky

        self.leds.thinking()
        reply = ""
        response = ""
        try:
            args = {
                'model': self.model,
                'messages': self.memory
            }
            if max_tokens:
                args['max_tokens'] = max_tokens

            if tools:
                args['tools'] = tools

            response = self.client.chat.completions.create(**args)
            print(str(response))
            if response.choices[0].message.content:
                reply = response.choices[0].message.content
                self.memory.append({"role": "assistant", "content": reply},) # overwrite reply

            if (response.choices[0].finish_reason) == "tool_calls":
                tool_call =  response.choices[0].message.tool_calls[0]
                self.memory.append(response.choices[0].message)

                call ='self.'+ tool_call.function.name +"(" + tool_call.function.arguments+ ")"

                reply = eval(call)
                self.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": "success"},)
                (user_input, max_tokens, tools) = self.HandleResponse(False, reply)
                response = self.client.chat.completions.create(model=this_model, messages=self.memory, max_tokens=max_tokens)
                if response.choices[0].message.content:
                    reply = response.choices[0].message.content
                    self.memory.append({"role": "assistant", "content": reply},) # overwrite reply

        except Exception as e:

            reply = f"There was an error talking to OpenAI. {str(e)}"
            self.memory.pop()  #get rid of that bad membry!

        self.leds.off()
        return str(reply.encode('ascii', 'ignore').decode("utf-8"))

    #NOte: this function alters the memory
    def HandleResponse(self, class_resp, user_input, canParaphrase=False):
#       The parent class handled the input.  
#       Unless told to paraphrase, return
        max_tokens = 500*self.token_mult
        local_tools = {}
        if class_resp:
            if class_resp == "goodbye": # allow the AI to say goodbye
                user_input =  "I have to go now, goodbye"
            if canParaphrase and not cf.g('SAVE_TOKENS'):  # something to paraphrase
                user_input = "Paraphrase '"+class_resp+"'"
            if not class_resp[0].isalpha(): # contains instructions (!, #, @)
                user_input = class_resp
            else:
                return (False, False, False)

#        return "ChatGPT: '"+user_input+"'"  # uncomment to test without using tokens
        role = "user"
        ret_tools = {}
        if user_input[:1] == '>': #text
            user_input = user_input[1:]

        #reply is a command 
        elif user_input[:1] == '!': #command
             role = "assistant"
             this_model = self.slow_model
             user_input = user_input[1:]
             self.memory.append({"role": role, "content": user_input},)
             max_tokens=100*self.token_mult  #75 words - keep it short for spontanous uttering

        #reply is a command 
        elif user_input[:1] == '^': #write memories
             role = "assistant"
             user_input = user_input[1:]
             self.memory.append({"role": role, "content": user_input},)
             max_tokens=1000*self.token_mult

        #reply is a picture
        elif user_input[:1] == '#': #picture-- TODO!!!
             print(user_input)
             (x, user_input, url) = user_input.split('#')
             self.memory.append({"role": role,
                  "content": [{"type": "text", "text": user_input + ", briefly describe the subject and say what you think"}, 
                              {"type": "image_url", "image_url": {"url": url,}, },],
                  })

        #reply is jusst text
        else:
             self.memory.append({"role": role, "content": user_input},)
             ret_tools = self.tools

        return (user_input, max_tokens, ret_tools)

    #ON Startup
    def Hello(self):
        return self.respond(f"!The user's name is {cf.g('USERNAMEP')}, say hello.")

    # On Wake State return greeting
    def WakeMessage(self):
        resp = "!The user just called to you."
        return self.respond(resp)

    # From Sleep State return greeting
    def Greet(self):
          resp = "!The user just returned just returned after "+AI.PrettyDuration(self, datetime.now() - self.last_user_interaction) +", greet them."
          return self.respond(resp)
    
    def Think(self):      
        return AI.Think(self)
        
    def InitiateConvo(self):
        print("initialte convo")
        ret = self.ProcessMessages()
        if not ret:
            ret = f"!Ask the user how thier {AI.TimeOfDay(self)} is going."
#        return ret
        return self.respond(ret)

    # called from init convo -- do not process (InitCOnvo will process)
    def ProcessMessages(self):
       ret = ""
       for m in  self.messages.GetMessages():
            message = m[1]
#            ret = responces_past[m[0]] % message
       return ret


    def SetEvent(self, event):  # DOTO maek this generic.  Allow push into messages
        return "!"+AI.SetEvent(self, event)

    def TakePicture(self, context):
        print("Calling Taking Picture from ChatGPT")
        url = self.eyes.SendPicture()
        try:
            return f"#{eval(str(context))['picture_context']}#{url}"
        except Exception as e:
            print("0 Didn't work: " + str(e))
        return f"#{context}#{url}"
 
    def Intruder(self):
        AI.Intruder(self)
        return self.respond("!There is an intruder in the house!  Threaten them and order them to leave.")
        #email URL

    def SaveMemories(self):
        memStr = self.respond(f"^Summarize your history with {cf.g('USERNAME')} in a single paragraph of 500 words or less to be used later as your memory.  FOcus on key events and topics.")
        memStr = ''.join(memStr.splitlines())
        self.memory = [
            {"role": "system", "content": cf.g('BACKSTORY')}, 
            {"role": "system", "content": memStr},
        ]
        print(memStr)
        cf.s('HISTORY', memStr)
        return memStr

    def Close(self):
       AI.Close(self)
       self.SaveMemories()
       # Remember the last convo
       return


    def get_emotion(self):
        return self.respond("in one word does user feel happy, sad, afraid or angry?")

class AI_ChatGPT(AI_OpenAI):

    base_url = ""
    model= cf.g('CHATGPT_MODEL')
    slow_model=cf.g('CHATGPT_MODEL_SLOW')
    api_key=cf.g('OPEN_AI_API_KEY')
    name = "Chat GPT"
    tools = False # turn this on if asked
    token_mult = 1
    
    def __init__(self):
        AI_OpenAI.__init__(self)
        print("AI ChatGPT loaded")


class AI_Llama(AI_OpenAI):

    base_url = "https://api.llama-api.com"
    api_key =cf.g('LLAMA_KEY')
    model =cf.g('LLAMA_MODEL')
    slow_model=cf.g('LLAMA_MODEL_SLOW')    
    name = "Llama"
    tools = False
    token_mult = 0.5
    def __init__(self):
        AI_OpenAI.__init__(self)
        print("AI Llama loaded")

class AI_Gemma(AI_Llama):
    model = cf.g('GEMMA_MODEL')
    slow_model = cf.g('GEMMA_MODEL_SLOW')
    name = "Gemma"

class AI_Qwen(AI_Llama):
    model = cf.g('QWEN_MODEL')
    slow_model = cf.g('QWEN_MODEL_SLOW')
    name = "Qwen"

class AI_Local(AI_OpenAI):
    base_url = "http://localhost:11434/v1"
    api_key = "unused"
    model = 'qwen2:0.5b'
    slow_model=model
    name = "Local"

class AI_Corgi(AI_OpenAI):
    base_url = "http://192.168.15.58:11434/v1"
    api_key = "unused"
    model = 'llama3.1:8b'
    slow_model=model
    name = "Corgi"

    def __init__(self):
        AI_OpenAI.__init__(self)
        print(f"{self.name} loaded")

class AI_Adhoc(AI_OpenAI):
    base_url = ""
    api_key = ""
    model = ''
    slow_model=model
    tools = {}
    token_mult = 1
    name = "AD Hoc"

    def __init__(self):
        AI_OpenAI.__init__(self)
        print("Enter the base url, including http: ")
        self.base_url = input()

        print("Enter the model name: ")
        self.model = input()
        self.model_slow = input()

        print("Enter the API Key, or leave blank to use OpenAI Key: ")
        self.key = input()
        if not self.key:
            self.key = cf.g('OPEN_AI_API_KEY')
         
        print(f"{self.name} loaded")



if __name__ == '__main__':
#    from camera_tools import Camera
#    eyes = Camera()
 
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
 
    ai = AI_Local()
    ai.leds = LEDS()
#    print(ai.respond("lets take my picture?"))
#     ai.Greet()
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

    ai.Close()

