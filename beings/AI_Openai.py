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
from error_handling import *
# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

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
        "name": "TakePictureToolCall",
        "description": "Take a picture with the attached camera.  Call when the user indicates they want you to look at something or see where they are.",
        "parameters": {
            "type": "object",
            "properties": {
                "picture_context": {
                    "type": "string",
                    "description": "The description and context of the picture subject.",
                },
            },
            "required": ["picture_subject"],
            "additionalProperties": False,
        }
     }
  }
]



class AI_openAI(AI):
    base_url = ""
    api_key = ""
    name = ""
    token_mult = 1
    tools = False

    def __init__(self):
        AI.__init__(self)
        if self.base_url:
            self.client = openai.Client(api_key=self.api_key,base_url=self.base_url)
        else:
            self.client = openai.Client(api_key=self.api_key,)
        self.memory = [ 
            {"role": "system", "content": f"Your name is {cf.g('AINAME')}. {cf.g('BACKSTORY')}"}, 
            {"role": "system", "content": 'Your history with the user: '+cf.g('HISTORY')},
        ]
        LogInfo(f"AI {self.name}, ({self.model()}) loaded.")
        return

    def model(self, vision=False):
        if vision:
            try:
                return cf.g(self.vision_model_key)
            except:
                pass # key doens't exsitst
        return cf.g(self.model_key)

    def respond(self, user_input, canParaphrase=False):
        self.face.thinking()
        class_resp = AI.respond(self, user_input)  # will return either a response
        (user_input, max_tokens, tools) = self.HandleResponse(class_resp, user_input)
        if not user_input:
            self.face.off()
            return class_resp #hacky

        reply = ""
        response = ""
        #TODO: call update!
        try:
            args = {
                'model': self.model(),
                'messages': self.memory,
                'temperature': cf.g('TEMPERATURE')
            }
            if max_tokens:
                args['max_tokens'] = max_tokens

            if tools:
                args['tools'] = tools
            LogDebug("Input: " + str(self.memory[-1]))
            response = self.client.chat.completions.create(**args)
            LogDebug("\n\nResponce: " + str(response))

            if response.choices[0].message.content:
                reply = response.choices[0].message.content
                self.memory.append({"role": "assistant", "content": reply},) # overwrite reply
                self.TrainData(user_input, reply)

            if (response.choices[0].finish_reason) == "tool_calls":
                tool_call =  response.choices[0].message.tool_calls[0]
                self.memory.append(response.choices[0].message)

                call ='self.'+ tool_call.function.name +"(" + tool_call.function.arguments+ ")"

                reply = eval(call)
                self.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": "success"},)
                (user_input, max_tokens, tools) = self.HandleResponse(False, reply)
                response = self.client.chat.completions.create(cf.g(self.model()), messages=self.memory, max_tokens=max_tokens)
                if response.choices[0].message.content:
                    reply = response.choices[0].message.content
                    self.memory.append({"role": "assistant", "content": reply},) # overwrite reply
        except Exception as e:

            reply = f"There was an error talking to OpenAI. {str(e)}"
            self.memory.pop()  #get rid of that bad membry!

        self.face.off()
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
             (x, user_input, file, url) = user_input.split('#')
             self.memory.append({"role": role,
                  "content": [{"type": "text", "text": user_input}, 
                              {"type": "image_url", "image_url": {"url": url,}, },],
                  })

        #reply is jusst text
        else:
             self.memory.append({"role": role, "content": user_input},)
             ret_tools = self.tools

        return (user_input, max_tokens, ret_tools)

    def TakePictureToolCall(self, context):
        LogInfo("Calling Taking Picture from ChatGPT")
        file = self.TakePicture()
        url = self.eyes.UploadPicture(file)
        LogInfo(f"URL: {url}")
        try:
            return f"#{eval(str(context['picture_context']))}#{file}#{url}"
        except Exception as e:
            LogWarn("eval() Didn't work: " + str(e))
            LogDebug(str(context))
        self.face.off()
        return f"#{context}#{file}#{url}"

    #ON Startup
    def Hello(self):
        return self.respond(f"!The user's name is {cf.g('USERNAMEP')}, say hello.")

    # On Wake State return greeting
    def WakeMessage(self):
        resp = "!The user just called to you."
        return self.respond(resp)

    # From Sleep State return greeting
    def Greet(self):
          if self.TimeOfDay() == "morning" and ((datetime.now() - self.last_user_interaction).total_seconds() / 3600) > 6:
              resp = "!The user just woke up for the day, say good morning."

          else: resp = "!The user just returned just returned after "+AI.PrettyDuration(self, datetime.now() - self.last_user_interaction) +", greet them."
          return self.respond(resp)
    
    def Think(self):      
        return AI.Think(self)
        
    def InitiateConvo(self, topic=""):
        LogInfo("initialte convo")
        if topic: ret = f"!The user looked {topic}, ask about that."
        else: ret = f"!Ask the user how thier {AI.TimeOfDay(self)} is going."
#        return ret
        return self.respond(ret)


    def SetEvent(self, event):  # DOTO maek this generic.  Allow push into messages
        return "!"+AI.SetEvent(self, event)

    def Intruder(self):
        AI.Intruder(self)
        return self.respond("!There is an intruder in the house!  Threaten them and order them to leave.")
        #email URL

    def SaveMemories(self):
        memStr = self.respond(f"^Summarize your history with {cf.g('USERNAME')}.  Fcus on key events and topics.  Return the answer in a single short paragraph of 500 words or less to be used later as your memory log")
        memStr = ''.join(memStr.splitlines())
        self.memory = [
            {"role": "system", "content": cf.g('BACKSTORY')}, 
            {"role": "system", "content": memStr},
        ]
        cf.s('HISTORY', memStr)
        return memStr

    def Close(self):
       AI.Close(self)
       self.SaveMemories()
       return

class AI_ChatGPT(AI_openAI):

    api_key=cf.g('OPEN_AI_API_KEY')
    model_key = 'CHATGPT_MODEL'
    slow_model_key = 'CHATGPT_MODEL_SLOW'
    name = "ChatGPT"
    tools = function_tools # False # turn this on if asked
    token_mult = 1
    training = True
    
    def __init__(self):
        AI_openAI.__init__(self)

class AI_Llama(AI_openAI):
    base_url = cf.g('LLAMA_BASE_URL')
    api_key = cf.g('LLAMA_KEY')
    model_key = 'LLAMA_MODEL'
    slow_model_key = 'LLAMA_MODEL_SLOW'
    name = "Llama"
    tools = False
    token_mult = 0.5

class AI_Gemma(AI_Llama):
    model_key = 'GEMMA_MODEL'
    slow_model_key = 'GEMMA_MODEL_SLOW'
    name = "Gemma"

class AI_Qwen(AI_Llama):
    model_key = 'QWEN_MODEL'
    slow_model_key = 'QWEN_MODEL_SLOW'
    name = "Qwen"

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
 
 
    ai = AI_ChatGPT()
    ai.leds = LEDS()
    ai.face = LEDS()
#    print(ai.respond("lets take my picture?"))
#     ai.Greet()
#    ai.WakeMessage()
#    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
#    user_inp  = "hello"
#    print(ai.Hello())
#    user_inp = "#this is a picture of me, waht do you think?#temp/capture_0_20240912133342132801.jpg#http://el3ktra.el3ktra.net/uploads/capture_0_20240911223907988147.jpg"
#    out = ai.respond(user_inp)
#    print(f'AI: {out}')

    user_inp = ""
    while user_inp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')

    ai.Close()
