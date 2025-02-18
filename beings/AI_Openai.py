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
from function_tools import function_tools
# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

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
        if self.IsConvoDirty(): self.memory = self.LoadConvo()
        
        start = datetime.now()
        ret = self.ai_respond(user_input)
        LogInfo(f"Completed request in {(datetime.now()-start).total_seconds()}s")
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
                'messages': self.GetMemory()
            }

            if max_tokens: args['max_tokens'] = max_tokens
            if tools: args['tools'] = tools
            if self.use_temp: args['temperature'] = cf.g('TEMPERATURE')
            if stream and not self.tools: args['stream'] = True  # could set to false if tools are used
            
            if stream: reply, response = self.reply_async(args)
            else: reply, response = self.reply_sync(args)

            LogDebug(response)
            if response:
                self.memory.append({"role": "assistant", "content": reply}) # save reply
                self.TrainData(user_input, reply)

                if response.choices[0].finish_reason == "tool_calls":

                     # append the tool call reply
                    tool_call =  response.choices[0].message.tool_calls[0]
                    self.memory.append(response.choices[0].message)    # from https://platform.openai.com/docs/guides/function-calling
                    self.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": "success"},)

                    # get tool call data
                    reply = eval('self.'+ tool_call.function.name +"(" + tool_call.function.arguments+ ")")
                    LogDebug(f"Tool call result: {reply}")

                    # append the message
                    (user_input, max_tokens, tools, streamx) = self.HandleResponse(False, reply) # reply contains result of ttol call
                    LogDebug(f"Sending image: {self.memory[-1]}")
                    args = {'model': self.model(), 'messages':self.GetMemory()}
                    if max_tokens:    args['max_tokens']  = max_tokens
                    if self.use_temp: args['temperature'] = cf.g('TEMPERATURE')

                    try:
                        response = self.client.chat.completions.create(**args)
                        LogDebug(f"Response from tool call: {response}")
                        if response.choices[0].message.content:
                            reply = self.StripActions(response.choices[0].message.content)
                            self.memory.append({"role": "assistant", "content": reply},)
                            stream=False # force return of data
                        else: LogWarn("No mesage in responce!")
                    except Exception as e:
                        LogError(f"There was an error sending the Tool Call result. {str(e.args)}")
                        reply = f"There was an error handling an OpenAI Tool Call. Check the logs."
                        self.memory.pop()  # get rid of tool call
                        self.memory.pop()  # get rid of the memory that called the tool call!


            else: LogWarn(f"AI_Openai: Didn't get response")
        except Exception as e:
            LogError(f"There was an error talking to OpenAI. {str(e.args)}")
            reply = f"There was an error talking to OpenAI. Check the logs."
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

        resp = False
        for chunk in response:
            if not resp: resp = chunk
            LogDebug(f"Async: {chunk}")
            m = chunk.choices[0].delta.content
            finish = chunk.choices[0].finish_reason
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
        resp.choices[0].finish_reason = finish
        return self.StripActions(full_reply), resp # always strip reply when async


    def reply_sync(self, args, should_strip=True):

#        ai_msg = self.client.invoke(input=args['messages'], kwargs=args)
#        reply = ai_msg.content
        reply = ""
        response = self.client.chat.completions.create(**args)
        if response.choices:
            reply =  response.choices[0].message.content
            if not reply: reply = ""
        LogDebug("Sync: " + str(response))
        if should_strip: return self.StripActions(reply), response
        else: return reply, response


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
            self.memory.append({"role": role, "content": user_input},)

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

        #reply is just text
        else:
             self.memory.append({"role": role, "content": user_input})
             ret_tools = self.tools

        return (user_input, max_tokens, ret_tools, stream)

    def GetString(self, key):
        return cf.g(key)

    def GetMemory(self):
         return self.memory
#        slice = -1 * min(len(self.memory)-2, cf.g('HISTORY_LOOKBACK'))
#        return self.memory[3:] + self.memory[slice:]

    def TakePictureToolCall(self, context):
        LogInfo("Calling Taking Picture from ChatGPT")
        file = self.TakePicture()
        url = self.eyes.UploadPicture(file)
        LogInfo(f"URL: {url}")
        try:
            d =  json.loads(str(context).replace("'", '"'))
            LogDebug(f"Pict context: {d['picture_context']}")
            context = d['picture_context']
        except Exception as e:
            LogWarn(f"json.loads Didn't work: {e.args}")
            context = str(context)
        self.face.off()
        return f"#{context}#{file}#{url}"

    #ON Startup
    def Hello(self):
#        return self.respond(f"!{cf.g('GREET_STR').format(cf.c('USERNAMEP', 'USERNAME'), AI.PrettyDuration(self, datetime.now() - self.last_user_interaction))}")
        return self.respond(f"!{cf.g('HELLO_STR').format(cf.c('USERNAMEP', 'USERNAME'))}")

    # On Wake State return greeting
    def WakeMessage(self):
        resp = "!{cf.g('WAKE_STR')}"
        return self.respond(resp)

    # From Idle State return greeting when user seen
    def Greet(self):
          if (self.LastAIInteraction() / 3600) > cf.g('AWAY_HOURS'):  # haven't talked to the user in more then 6 hours
              if self.TimeOfDay() == "morning":   return self.respond(f"!{cf.g('MORNING_STR')}")
              elif self.TimeOfDay() == "afternoon": return self.respond(f"!{cf.g('AFTERNOON_STR')}")
              elif self.TimeOfDay() == "evening": return self.respond(f"!{cf.g('EVENING_STR')}")

          if self.TimeOfDay() == "night": return self.respond(f"!{cf.g('NIGHT_STR')}")
          else: return self.InitiateConvo()

    def Think(self):
        # when the memory gets too full, reset it.
#        if len(self.memory)>cf.g('HISTORY_LOOKBACK'):
#            self.memory = self.GetMemory()
#            self.face.thinking()
#            self.memory = self.LoadConvo(read=False)
#            self.face.off()
        return AI.Think(self)

    def InitiateConvo(self, mood=""):
        if mood: return self.respond(f"!{cf.g('MOOD_STR').format(mood)}")
        elif random.randint(0, 5) == 1:
            path = self.TakePicture(0, selfie=True)
            if path:
                url  = self.eyes.UploadPicture(path)
                desc = f"{cf.g('CAMERA_CONVO_STR')}"
                return self.respond(f'#!{desc}#{path}#{url}') # force async
        return self.respond(f"!{cf.g('CONVO_STR').format(self.TimeOfDay())}")


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
            f = open(filename, 'w')
        except Exception as e:
           LogError(f"WriteConvo exception opening file for writing: {str(e)}")
           return False
        try:
            i = 0
            while i < len(self.memory):
                m = self.memory[i]
                if i < (len(self.memory)-1): next = self.memory[i+1]
                else: next = None

                try:
                    if m['role']=='assistant': f.write(f"|{m['content']}\n")
                    elif m['role']=='user' and next and next['role']=='assistant':
                        f.write(f"{m['content']}|{next['content']}\n")
                        i = i+1
                except:
                    LogWarn(f"WriteConvo: item not indexable: {m}")
                    pass  # not indexable
                i = i+1
            f.close()
            os.system(f"sudo chown www-data:www-data {filename} training ; sudo chmod ug+rw {filename}; sudo chmod ug+rwx training")
            self.last_convo_load = datetime.now()
            LogDebug(f"Conversation Appended to '{filename}'.")
            return True
        except Exception as e:
            LogError(f"WriteConvo exception opening file for writing: {str(e)}")
            return False

    def LoadConvo(self, init=True):
        LogInfo(f"Loading conversation...")
        convo = self.ReadConvo()
        if init: memory = self.InitMemory() + convo
        else: memory = convo
#        if read: history = self.ReadConvo()
#        else: history = self.memory[3:]  # use own history, skip first three system commands

#        history = self.SumMemory(convo)
#        LogDebug(f"History: {history}")
#        memory.append({"role": "system", "content": "You wrote this history with the user:" +  history})
        return memory

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

    def InitMemory(self, includeHistory=True):
        memory = [{"role": "system", "content": cf.g('BACKSTORY')}, {"role": "system", "content": cf.g('INSTRUCTION')}]
        if includeHistory: memory.append({"role": "system", "content": f"You wrote this about your history with {cf.g('USERNAME')}: '{cf.g('HISTORY')}'"})
        return memory

    def SetEvent(self, event):  # DOTO maek this generic.  Allow push into messages
        return "!"+AI.SetEvent(self, event)

    def Intruder(self):
        AI.Intruder(self)
        return self.respond(f"!{cf.g('INTRUDER_STR')}")
        #email URL

    def SaveMemories(self, memory=False):  # called on close
        if not memory:
            self.memory = self.memory[3:]
        else: self.memory = memory
        memStr = self.ai_respond(f"^{cf.g('HISTORY_STR').format(cf.g('USERNAME'))}")
        memStr = ''.join(memStr.splitlines())
        cf.w('HISTORY', memStr)
        return memStr

    def SumMemory(self, memory=False): # unused
        if not memory: memory = self.memory[2:]  # skip system instructions when using own memory

        memory.append({"role": "user", "content": f"Summarize the above {len(memory)} items, focusing on facts (namely about the user), upcoming events, current and future projects, and frequent topics.  Be detailed and comprehensive.  This will be saved to reshresh your memory the next time you talk."})
        args = {
            'model': self.model(),
            'messages': memory,
        }
#        sum = self.reply_sync(args, False) # don't strip response
        response = self.client.chat.completions.create(**args)
        if response.choices:
            return response.choices[0].message.content

    def Close(self):
       AI.Close(self)
#       self.WriteConvo()
       self.SaveMemories()  # don't save into converstaion file
       return

class AI_ChatGPT(AI_openAI):

    api_key=cf.g('OPEN_AI_API_KEY')
    model_key = 'CHATGPT_MODEL'
    slow_model_key = 'CHATGPT_MODEL_SLOW'
    name = "ChatGPT"
    tools = False # function_tools # False # turn this on if asked
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
        AI.__init__(self) 
        self.client=openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.memory = self.LoadConvo()
        return

class AI_Grok(AI_openAI):

    tools = False
    token_mult = 1
    base_url = cf.g('GROK_URL')
    api_key = cf.g('GROK_API')
    model_key = 'GROK_MODEL'
    slow_model_key = model_key
    name = "Grok"

class AI_Llama(AI_openAI):
    base_url = cf.g('LLAMA_BASE_URL')
    api_key = cf.g('LLAMA_KEY')
    model_key = 'LLAMA_MODEL'
    slow_model_key = 'LLAMA_MODEL_SLOW'
    name = "Llama"
    tools = False
    token_mult = 0.5
    use_temp = False

if __name__ == '__main__':
#    from camera_tools import Camera
#    eyes = Camera()
 
    global STATE
    from face import DummyFace
    STATE.ChangeState('Idle')
    ai = AI_Llama()
    ai.face = DummyFace()

    user_inp = ""
    while not STATE.ShouldQuit():
        user_inp = "^" + input(f"{cf.g('USERNAME')}: ")
        print(f'{cf.g("AINAME")}: {ai.respond(user_inp)}')

#    ai.Close()
