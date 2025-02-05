import json
import os
import sys
import re
import inspect
import threading
from pathlib import Path
from datetime import datetime, timedelta
import openai
import llamaapi
import random
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
    model_key = ''
    vision_model_key = ''
    has_vision = True
    memory = []
    last_convo_load = datetime.now()
    use_temp = True

    def __init__(self):
        AI.__init__(self)
        if self.base_url:
#            self.client = openai.Client(api_key=self.api_key,base_url=self.base_url)
            self.client=openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = openai.Client(api_key=self.api_key,)


        self.memory = self.LoadConvo()
        LogInfo(f"AI {self.name}, ({self.model()}) loaded.")
        return

    def model(self, vision=False):
        if vision: return cf.c(self.vision_model_key, self.model_key)
        else: return cf.g(self.model_key)

    def respond(self, user_input):
#        if self.IsConvoDirty(): self.memory = self.LoadConvo()
        
        ret = self.ai_respond(user_input)

        # start the write config thread (while we are listening)
        write_convo_thread = threading.Thread(target=self.WriteConvo, daemon=True)
        write_convo_thread.name = f"{GetHostname()} WriteConvoThread"
        write_convo_thread.start()

        return ret


    def ai_respond(self, user_input, canParaphrase=False):
        self.face.thinking()
        class_resp = AI.respond(self, user_input)  # will return either a response
        (user_input, max_tokens, tools, stream) = self.HandleResponse(class_resp, user_input)
        if not user_input:
            self.face.off()
            return class_resp #hacky

        reply = ""

        try:
            args = {
                'model': self.model(),
                'messages': self.memory,
            }

            if max_tokens: args['max_tokens'] = max_tokens
            if tools: args['tools'] = tools
            if self.use_temp: args['temperature'] = cf.g('TEMPERATURE')
            if stream: args['stream'] = True

            if stream: reply, response, finish = self.reply_async(args)
            else: reply, response, finish = self.reply_sync(args)

            if response:
                self.TrainData(user_input, reply)

                if (response.choices[0].finish_reason) == "tool_calls":
                    tool_call =  response.choices[0].message.tool_calls[0]
                    self.memory.append(response.choices[0].message)

                    call ='self.'+ tool_call.function.name +"(" + tool_call.function.arguments+ ")"

                    reply = eval(call)
                    self.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": "success"},)
                    (user_input, max_tokens, tools, ) = self.HandleResponse(False, reply)
                    response = self.client.chat.completions.create(cf.g(self.model()), messages=self.memory, max_tokens=max_tokens)
                    if response.choices[0].message.content:
                        reply = response.choices[0].message.content
                        self.memory.append({"role": "assistant", "content": reply},) # overwrite reply
            else: LogWarn(f"AI_Openai: Didn't get response")
        except Exception as e:
            reply = f"There was an error talking to OpenAI. {str(e)}:{str(e.args)}"
            self.memory.pop()  #get rid of that bad membry!
            stream=False
        self.face.off()
        if stream: return ""
        return str(reply.encode('ascii', 'ignore').decode("utf-8"))

    def reply_async(self, args):
        reply = ""
        full_reply = ""
        finish = ""
        resp = ""
        face = self.face
        response = self.client.chat.completions.create(**args)

        #if this is a picture we are talking about, leave it on the screen
#        if args['model']==self.model(vision=True):
        if cf.g('GIVE_PICT_DESC') in str(args['messages'][-1]):
            face=None            # don't allow mouth to control the face
            self.face.looking()  # turn the screen

        for chunk in response:
            m = chunk.choices[0].delta.content
            finish = chunk.choices[0].finish_reason
            resp = chunk
            if m:
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
        return self.StripActions(full_reply), resp, finish


    def reply_sync(self, args, should_strip=True):

#        ai_msg = self.client.invoke(input=args['messages'], kwargs=args)
#        reply = ai_msg.content
        reply = ""
        response = self.client.chat.completions.create(**args)
        if response.choices:
            reply =  response.choices[0].message.content
        LogDebug("Sync: " + str(response))
        if should_strip: return self.StripActions(reply), response, response.choices[0].finish_reason
        else: return self.StripActions(reply), response, response.choices[0].finish_reason


    #NOte: this function alters the memory
    def HandleResponse(self, class_resp, user_input, canParaphrase=False):
#       The parent class handled the input.  
#       Unless told to paraphrase, return
        stream = True
        max_tokens = 500*self.token_mult

        if class_resp:
            if canParaphrase and not cf.g('SAVE_TOKENS'):  # something to paraphrase
                user_input = "Paraphrase '"+class_resp+"'"
            if not class_resp[0].isalpha(): # contains instructions (!, #, @)
                user_input = class_resp
            else:
                return (False, False, False, False)

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
             stream=False

        #reply is an command 
        elif user_input[:1] == '^': #write memories
             role = "assistant"
             user_input = user_input[1:]
             self.memory.append({"role": role, "content": user_input},)
             max_tokens=1000*self.token_mult
             stream=False

        #reply is a picture
        elif user_input[:1] == '#': #picture-- TODO!!!
             (x, user_input, file, url) = user_input.split('#')
             self.memory.append({"role": role,
                  "content": [{"type": "text", "text": user_input}, 
                              {"type": "image_url", "image_url": {"url": url,}, },],
                  })

        #reply is jusst text
        else:
             self.memory.append({"role": role, "content": user_input})
             ret_tools = self.tools

        return (user_input, max_tokens, ret_tools, stream)

    def GetString(self, key):
        return cf.g(key)


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
#        return self.respond(f"!{cf.g('GREET_STR').format(cf.c('USERNAMEP', 'USERNAME'), AI.PrettyDuration(self, datetime.now() - self.last_user_interaction))}")
        return self.respond(f"!{cf.g('HELLO_STR').format(cf.c('USERNAMEP', 'USERNAME'))}")

    # On Wake State return greeting
    def WakeMessage(self):
        resp = "!{cf.g('WAKE_STR').format(cf.c('USERNAMEP', 'USERNAME'))}"
        return self.respond(resp)

    # From Idle State return greeting when user seen
    def Greet(self):
          self.WriteConvo()
          self.LoadConvo()  # reset the conversation 
          if (self.LastAIInteraction() / 3600) > cf.g('AWAY_HOURS'):  # haven't talked to the user in more then 6 hours
              if self.TimeOfDay() == "morning":   return self.respond(f"!{cf.g('MORNING_STR').format(cf.c('USERNAMEP', 'USERNAME'))}")
              elif self.TimeOfDay() == "afternoon": return self.respond(f"!{cf.g('AFTERNOON_STR').format(cf.c('USERNAMEP', 'USERNAME'))}")
              elif self.TimeOfDay() == "evening": return self.respond(f"!{cf.g('EVENING_STR').format(cf.c('USERNAMEP', 'USERNAME'))}")

          if self.TimeOfDay() == "night": return self.respond(f"!{cf.g('NIGHT_STR').format(cf.c('USERNAMEP', 'USERNAME'))}")
          else: return self.InitiateConvo()

    def Think(self):
        # when the memory gets too full, reset it.
        if len(self.memory)>5:
            self.face.thinking()
            self.memory = self.LoadConvo(read=False)
            self.face.off()
        return AI.Think(self)

    def InitiateConvo(self, mood=""):
        if mood: return self.respond(f"!{cf.g('MOOD_STR').format(cf.c('USERNAMEP', 'USERNAME'), mood)}")
        elif random.randint(0, 5) == 1:
            path = self.TakePicture(0, selfie=True)
            if path:
                url  = self.eyes.UploadPicture(path)
                desc = f"{self.GetString('CAMERA_CONVO_STR').format(cf.g('USERNAME'))}"
                return self.respond(f'#!{desc}#{path}#{url}') # force async
        return self.respond(f"!{cf.g('CONVO_STR').format(cf.c('USERNAMEP', 'USERNAME'), AI.TimeOfDay(self))}")


    def IsConvoDirty(self):
        try:
            f_dt = datetime.fromtimestamp(os.path.getmtime("training/AI_"+self.name + "_convo.dat"))
            if f_dt > self.last_convo_load:
                return True
        except Exception as e:
            LogWarn(f'IsConvoDirty Caught Exception: {e.args}')
        return False

    def WriteConvo(self):
        filename = "training/AI_"+self.name + "_convo.dat"
        try:
            f = open(filename, 'a')
        except Exception as e:
           LogError(f"WriteConvo exception opening file for writing: {str(e)}")
           return False
        try:
            i = 0
            while i < len(self.memory):
                m = self.memory[i]
                if i < (len(self.memory)-1): next = self.memory[i+1]
                else: next = None

                if m['role']=='assistant': f.write(f"|{m['content']}\n")
                elif m['role']=='user' and next and next['role']=='assistant':
                    f.write(f"{m['content']}|{next['content']}\n")
                    i = i+1

                i = i+1
            f.close()
            os.system(f"sudo chown el3ktra:www-data {filename} training ; sudo chmod ug+rw {filename}; sudo chmod ug+rwx training")
            self.last_convo_load = datetime.now()
            LogDebug(f"Conversation Appended to '{filename}'.")
            return True
        except Exception as e:
            LogError(f"WriteConvo exception opening file for writing: {str(e)}")
            return False

    def LoadConvo(self, init=True, read=True):
        LogInfo(f"Loading conversation...")
        if init: memory = self.InitMemory()
        else: memory = []

        if read: history = self.ReadConvo()
        else: history = self.memory[3:]  # use own history, skip first three system commands

        history = self.SumMemory(history)

        LogDebug(f"History: {history}")

        memory.append({"role": "system", "content": "You wrote this history with the user:" +  history})

        return memory #+ history


    def ReadConvo(self):
        memory = []

        filename = "training/AI_"+self.name + "_convo.dat"
        if os.path.exists(filename):
            try:
                f = open(filename, 'r')

                for line in f:
                    if "|" in line:
                        (user, system) = line.split("|")
                        if user:
                            memory.append({"role": "user", "content":user})
                        if system:
                            memory.append({"role": "assistant", "content":system.replace("\n", "")})
                f.close()
                LogInfo(f"Convo file loaded from '{filename}'")

            except Exception as e:
                LogError(f"WriteConvo exception opening file for writing: {str(e)}")
        else:
            LogWarn(f"No ConvoFile {filename}.")
        return memory

    def InitMemory(self, includeHistory=False):
        memory = [
            {"role": "system", "content": f"Your name is {cf.g('AINAME')}, and the user's name is {cf.g('USERNAME')}. {cf.g('BACKSTORY')}."},
            {"role": "system", "content": cf.g('INSTRUCTION')}
        ]
        if includeHistory: memory.append({"role": "system", "content": f"You wrote this about your history with {cf.g('USERNAME')}: '{cf.g('HISTORY')}'"})
        return memory

    def SetEvent(self, event):  # DOTO maek this generic.  Allow push into messages
        return "!"+AI.SetEvent(self, event)

    def Intruder(self):
        AI.Intruder(self)
        return self.respond(f"!{cf.g('INTRUDER_STR')}")
        #email URL

    def SaveMemories(self):
        memStr = self.ai_respond(f"^{cf.g('HISTORY_STR').format(cf.g('USERNAME'))}")
        memStr = ''.join(memStr.splitlines())
        self.memory = [
            {"role": "system", "content": cf.g('BACKSTORY')}, 
            {"role": "system", "content": memStr},
        ]
        cf.s('HISTORY', memStr)
        return memStr

    def SumMemory(self, memory=False):
        if not memory: memory = self.memory[2:]  # skip system instructions when using own memory

        memory.append({"role": "user", "content": f"Summarize the above {len(memory)} items, focusing on facts (namely about the user), upcoming events, current and future projects, and frequent topics.  Be detailed and comprehensive.  This will be saved to reshresh your memory the next time you talk."})
        args = {
            'model': self.model(),
            'messages': memory,
        }
        sum = self.reply_sync(args, False) # don't strip response
        return sum

    def Close(self):
       AI.Close(self)
       self.WriteConvo()
#       self.SaveMemories()  # don't save into converstaion file
       return

class AI_ChatGPT(AI_openAI):

    api_key=cf.g('OPEN_AI_API_KEY')
    model_key = 'CHATGPT_MODEL'
    slow_model_key = 'CHATGPT_MODEL_SLOW'
    name = "ChatGPT"
    tools = function_tools # False # turn this on if asked
    token_mult = 1
    training = True

class AI_Deepseek(AI_openAI):

    tools = False
    token_mult = 1
    base_url = cf.g('DEEPSEEK_URL')
    api_key = cf.g('DEEPSEEK_API')
    model_key = 'DEEPSEEK_MODEL'
    slow_model_key = model_key
    name = "Deepseek"

    def __init__(self):
        AI.__init__(self) # we don't want to init AI_OpenAI, we just want the functions
#        self.client = lc.ChatOllama(base_url =self.base_url, model=self.model(), temperature=cf.g('TEMPERATURE'))
        self.client=openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.memory = self.LoadConvo()
        return


class AI_Llama(AI_openAI):
    base_url = cf.g('LLAMA_BASE_URL')
    api_key = cf.g('LLAMA_KEY')
    model_key = 'LLAMA_MODEL'
    slow_model_key = 'LLAMA_MODEL_SLOW'
    name = "Llama"
    tools = False
    token_mult = 0.5
    use_temp = False

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
    from face import DummyFace
    STATE.ChangeState('Idle')
    ai = AI_ChatGPT()
    ai.face = DummyFace()

    user_inp = ""
    while not STATE.ShouldQuit():
        user_inp = input(f"{cf.g('USERNAME')}: ")
        print(f'{cf.g("AINAME")}: {ai.respond(user_inp)}')

#    ai.Close()
