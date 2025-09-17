import json
import os
import sys
import re
import inspect
import threading
from pathlib import Path
from datetime import datetime, timedelta
import openai
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
        self.client = openai.Client(api_key=self.api_key,)


        self.memory = self.LoadConvo()
        LogInfo(f"AI {self.name}, ({self.model()}) loaded.")
        return

    def model(self, vision=False):
        if vision and self.has_vision: return cf.c(self.vision_model_key, self.model_key)
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
            
            if stream:
                args['stream'] = True
                reply = self.reply_async(args)
            else: reply = self.reply_sync(args)

            if reply:
                self.memory.append({"role": "assistant", "content": reply}) # save reply
                self.TrainData(user_input, reply)

            else: LogWarn(f"AI_Openai: Didn't get response")
        except Exception as e:
            LogError(f"There was an error talking to OpenAI. {str(e.args)}")
            reply = f"There was an error talking to OpenAI. Check the logs."
            self.memory = self.memory[:-1]  #get rid of that bad membry!
            stream=False
        self.face.off()
        if stream: return ""  # dont reread last message read during async
        return str(reply.encode('ascii', 'ignore').decode("utf-8"))

    def reply_async(self, args):
        # tool calls
        tc = None
        ic_id = None
        tc_arg = ""

        reply = ""
        full_reply = ""
        finish = ""
        resp = ""
        face = self.face
        try:
            response = self.client.chat.completions.create(**args)
        except Exception as e:
            LogError(f"Caught exception creating response: {e.args}")
            return ""
        #if this is a picture we are talking about, leave it on the screen
#        if args['model']==self.model(vision=True):
        if cf.g('GIVE_PICT_DESC') in str(args['messages'][-1]):
            face=None            # don't allow mouth to control the face
            self.face.looking()  # turn the screen

        resp = False
        try:
            for chunk in response:
                if not resp: resp = chunk  # grab the firset chunk to be used below for tool calls
#                LogDebug(f"Async ch: {chunk}")
                m = chunk.choices[0].delta.content
                finish = chunk.choices[0].finish_reason
                if m:
                    full_reply = full_reply + m
                    eos = re.search(r"(^|[^.])(!|\.|\?)( |$)", m)
                    if eos:
                        reply = reply + m[:(eos.span()[0])+2]
                        self.mouth.say(self.StripActions(reply), face=face, asyn=True)
                        reply = m[(eos.span()[0])+2:]
                    else: reply = reply + m
                if chunk.choices[0].delta.tool_calls:
                    if chunk.choices[0].delta.tool_calls[0].function.arguments: tc_arg = tc_arg + chunk.choices[0].delta.tool_calls[0].function.arguments
                    if chunk.choices[0].delta.tool_calls[0].function.name:
                        tc = chunk.choices[0].delta.tool_calls[0].function.name
                        tc_id = chunk.choices[0].delta.tool_calls[0].id
    
            if finish == "tool_calls":
                LogDebug(f"Async Tool Call: {tc}({tc_arg})")
                self.memory.append(resp.choices[0].delta)    # from https://platform.openai.com/docs/guides/function-calling
                reply = self.HandleToolCall(tc, tc_id, tc_arg)
                full_reply = reply
            self.mouth.say(self.StripActions(reply), face=face, asyn=False)
        except Exception as e:
            LogError(f"Caught exception creating resonse: {e.args}")
            return ""

        if face: face.off()
        return self.StripActions(full_reply)
 

    def reply_sync(self, args, should_strip=True):

#        ai_msg = self.client.invoke(input=args['messages'], kwargs=args)
#        reply = ai_msg.content
        reply = ""
        response = self.client.chat.completions.create(**args)
        if response.choices:
            reply =  response.choices[0].message.content
            if not reply: reply = ""
        LogDebug("Sync: " + str(response))

        if response.choices[0].finish_reason == "tool_calls":
            # append the tool call reply
            name =  response.choices[0].message.tool_calls[0].function.name
            id =  response.choices[0].message.tool_calls[0].id
            argument =  response.choices[0].message.tool_calls[0].function.arguments
            self.memory.append(response.choices[0].message)    # from https://platform.openai.com/docs/guides/function-calling
            reply = self.HandleToolCall(name, id, argument)
        if should_strip: return self.StripActions(reply)
        else: return reply

    def HandleToolCall(self, name, id, arguments):

        self.memory.append({"role": "tool", "tool_call_id": id, "content": "success"},)

        # get tool call data
        reply = eval('self.'+ name +"(" + arguments+ ")")
        LogDebug(f"Tool call result: {reply}")

        # append the message
        (user_input, max_tokens, tools, streamx) = self.HandleResponse(False, reply) # reply contains result of ttol call
        LogDebug(f"Sending tool call: {self.memory[-1]}")
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
            self.memory = self.memory[:-2]  # get rid of tool call and memory that called the tool

        # save and reload the convo to remove the tool calls from memory
        self.WriteConvo()
        self.memory = self.LoadConvo()

        return reply
    
    #NOte: this function alters the memory
    def HandleResponse(self, class_resp, user_input):
#       The parent class handled the input.  
#       Unless told to paraphrase, return
        stream = True
        max_tokens = 500*self.token_mult

        if class_resp:
            if not class_resp[0].isalpha(): # contains instructions (!, #, @)
                user_input = class_resp
            else:
                return (False, False, False, False) # say the class responce

#        return "ChatGPT: '"+user_input+"'"  # uncomment to test without using tokens
        role = "user"
        ret_tools = {}
        if user_input[:1] == '>': #text
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": user_input},)

        if user_input[:1] == '~': #paraphrase
            user_input = user_input[1:]
            self.memory.append({"role": role, "content": "Paraphrase '"+class_resp+"'"},)

        #reply is a command
        elif user_input[:1] == '!': #command
#             role = "assistant"
             user_input = user_input[1:]
             self.memory.append({"role": role, "content": user_input},)
             max_tokens=100*self.token_mult  #75 words - keep it short for spontanous uttering
             stream=False

        #reply is an command
        elif user_input[:1] == '^': #write memories
#             role = "assistant"
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

    def NoResponse(self):
        if self.is_spontanous:
            self.is_spontanous = False
            LogDebug("No response.  Removing last two memories")
#            self.memory = self.memory[:-2]  
            del self.memory[-2:]
            self.WriteConvo()
            LogDebug(self.memory[:3])

    def GetString(self, key):
        return cf.g(key)

    def GetMemory(self):
#        return self.memory
        slice = -1 * min(len(self.memory)-2, cf.g('HISTORY_LOOKBACK'))
        if self.memory[0]['role']!='system':
            self.memory = self.InitMemory() + self.memory
        return self.memory[:3] + self.memory[slice:]

    def TakePictureToolCall(self, context):
        LogInfo(f"Calling Taking Picture from {self.name}")
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


    def Think(self):
        # when the memory gets too full, reset it.
#        if len(self.memory)>cf.g('HISTORY_LOOKBACK'):
#            self.memory = self.GetMemory()
#            self.face.thinking()
#            self.memory = self.LoadConvo(read=False)
#            self.face.off()
            #self.SaveMemories()
        return AI.Think(self)

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
                    LogWarn(f"WriteConvo: item not indexable: {m}") # will get thrown for tool calls
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

    def SaveMemories(self):  # called on close
        if len(self.memory) > 3:
            self.memory = self.memory[3:]
            memStr = self.ai_respond(f"^{cf.g('HISTORY_STR').format(cf.g('USERNAME'))}")
            memStr = ''.join(memStr.splitlines())
            cf.w('HISTORY', memStr)
            self.memory = self.InitMemory() + self.memory
        else: memStr = cf.g('HISTORY')
        return memStr

    def Close(self):
       self.SaveMemories()  # don't save into converstaion file
       self.WriteConvo()
       AI.Close(self)
       return

class AI_ChatGPT(AI_openAI):

    api_key=cf.g('OPEN_AI_API_KEY')
    model_key = 'CHATGPT_MODEL'
    slow_model_key = 'CHATGPT_MODEL_SLOW'
    name = "ChatGPT"
    tools = function_tools # False # turn this on if asked
    token_mult = 1
    training = True

class AI_OpenAIurl(AI_openAI):

    base_url  = ""

    def __init__(self):
        AI.__init__(self)
        self.client=openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.memory = self.LoadConvo()
        return

class AI_Grok(AI_OpenAIurl):
    tools = False
    token_mult = 1
    base_url = cf.g('GROK_URL')
    api_key = cf.g('GROK_API')
    model_key = 'GROK_MODEL'
    slow_model_key = model_key
    name = "Grok"
    has_vision = False

class AI_Llama(AI_OpenAIurl):
    base_url = cf.g('LLAMA_BASE_URL')
    api_key = cf.g('LLAMA_KEY')
    model_key = 'LLAMA_MODEL'
    slow_model_key = 'LLAMA_MODEL_SLOW'
    name = "Llama"
    tools = False
    token_mult = 1
    use_temp = False
    has_vision = False

class AI_Poe(AI_OpenAIurl):
    base_url = cf.g('POE_BASE_URL')
    api_key = cf.g('POE_KEY')
    model_key = 'POE_MODEL'
    slow_model_key = model_key
    name = "Poe"
    tools = False
    token_mult = 1
    use_temp = False
    has_vision = False

if __name__ == '__main__':
#    from camera_tools import Camera
    from speech_tools import DummySpeech
    from face import DummyFace
#    import pygame

#    pygame.mixer.init()
 #   eyes = Camera()

    global STATE
    SetErrorLevel(4)
    STATE.ChangeState('Idle')
    ai = AI_ChatGPT()
    ai.face = DummyFace()
  #  ai.eyes = eyes
    ai.mouth = DummySpeech()
    user_inp = ""
    while not STATE.ShouldQuit():
        user_inp = input(f"{cf.g('USERNAME')}: ")
        print(f'{cf.g("AINAME")}: {ai.respond(user_inp)}')

   # eyes.Close()
#    ai.Close()
