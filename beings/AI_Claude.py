import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import anthropic
from AI_class import AI
from AI_Openai import AI_openAI
import PIL
import base64
from error_handling import *
# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

class AI_Claude(AI_openAI):

    client = 0
    config=0

    model_key = 'CLAUDE_MODEL'
    name = "Claude"
    training = True
    has_vision = True

    def __init__(self):
        AI.__init__(self)


        self.client =  anthropic.Anthropic(api_key=cf.g('CLAUDE_API_KEY'))

#        self.Claude = genai.GenerativeModel(model_name=self.model,system_instruction=app_desc)     
#        self.config = genai.types.GenerationConfig(
#            max_output_tokens = 50,
#            temperature = 1.0  # higher numbers for more creative responces
#        )
        self.memory = self.LoadConvo(False)  # don''t init with system messages for this model
        return

    def ai_respond(self, user_input, canParaphrase=False):
        reply = ""
        file = False
        stream = True
        this_model = self.model
        class_resp = AI.respond(self, user_input)  # will return either a response
#       The parent class handled the input.  
#       Unless told to paraphrase, return

        if class_resp:
            if class_resp in ("return", "!", ""):
                return ""  # don't say anything
            elif class_resp == "goodbye": # allow the AI to say goodbye
                user_input =  "I have to go now, goodbye"
            elif not class_resp[0].isalpha(): # contains instructions (!, #, @)... we will skip
                user_input = class_resp
            else:
                return class_resp
#            elif canParaphrase and not cf.g('SAVE_TOKENS'):
#                user_input = "Paraphrase '"+class_resp+"'"

        if user_input[0] == '#':  # its a picture
            l = user_input.split('#') # none, desc, file, url
            file = None
            with open(l[2], "rb") as image_file: file = base64.b64encode(image_file.read()).decode("utf-8")
            user_input = [{"type": "image", "source":{"type": "base64", "media_type": "image/jpeg", "data": file}},{"type": "text", "text": l[1]}]
        elif user_input[0] == '~':  # its a picture
            user_input = f"Paraphrase '{user_input[1:]}'"
        elif user_input[0] == '!':  # its a command
            user_input = user_input[1:]
            stream = False
        elif not user_input[0].isalpha():
            user_input = user_input[1:]

        self.memory.append({"role": "user", "content": user_input})

        self.face.thinking()
        try:
            if stream:
                rep = ""
                with self.client.messages.stream(model=self.model(), max_tokens=500, temperature=cf.g('TEMPERATURE'), system = f"{cf.g('BACKSTORY')}  {cf.g('INSTRUCTION')}", messages=self.GetMemory()) as stream:
                    for text in stream.text_stream:
                        reply = reply + text
                        eos = re.search(r"(^|[^.])(!|\.|\?)( |$)", text)
                        if eos:
                            rep = rep + text[:(eos.span()[0])+2]
                            self.face.talking()
                            self.mouth.say(self.StripActions(rep), face=self.face, asyn=True)
                            LogDebug("Async: " + str(text))
                            rep = text[(eos.span()[0])+2:]
                            self.face.thinking()
                        else: rep = rep + text
                self.mouth.say(self.StripActions(rep), face=self.face, asyn=False)
                self.face.off()
            else:
                message = self.client.messages.create(model=self.model(), max_tokens=500, temperature=cf.g('TEMPERATURE'), system = f"{cf.g('BACKSTORY')}  {cf.g('INSTRUCTION')}", messages=self.GetMemory())
                reply = message.content[0].text
            self.memory.append({"role": "assistant", "content": reply}) # overwrite reply
        except Exception as e:
            stream = False
            LogError(f"There was an error talking to Claude: {str(e.args)}")
            reply = f"There was an error talking to Claude."
        if file:
            LogDebug("deleting from memory pict: " + self.memory[-2]['content'][1]['text'])
            self.memory[-2]["content"]=user_input  # erase the picture
        self.face.off()

        if stream: return ""
        else: return reply

    def SumMemory(self, memory=False):
        if not memory: memory = self.memory[2:]  # skip system instructions when using own memory

        sys = f"Summarize the above {len(memory)} items, focusing on facts (namely about the user), upcoming events, current and future projects, and frequent topics.  Be detailed and comprhensive.  This will be saved to reshresh your memory the next time you talk."

        args = {
            'model': self.model(),
            'max_tokens': 1000,
            'messages': memory,
            'temperature': cf.g('TEMPERATURE'),
            'system':  sys
        }
#        sum = self.reply_sync(args, False) # don't strip response
        response = self.client.messages.create(**args)
        if response.content:
            return message.content[0].text



    def Close(self):
       AI.Close(self)  # prints memory
       return

if __name__ == '__main__':
   
    from speech_tools import DummySpeech
    from face import DummyFace
    import pygame

#    pygame.mixer.init()
#    eyes = Camera()

    global STATE
    SetErrorLevel(4)
    STATE.ChangeState('Idle')
    ai = AI_Claude()
    ai.face = DummyFace()
#    ai.eyes = eyes
    ai.mouth = DummySpeech()
    user_inp = ""
    while not STATE.ShouldQuit():
        user_inp = input(f"{cf.g('USERNAME')}: ")
        print(f'{cf.g("AINAME")}: {ai.respond(user_inp)}')

  #  eyes.Close()
