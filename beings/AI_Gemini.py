import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import google.generativeai as genai
import PIL.Image
from AI_class import AI

# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

responces_past = {
    "mood": 'earlier you saw the user looked %s. Ask them about that. ',
    "evesdrop": 'you heard the user say "%s" earlier. ask a follow up question'
}
  
responces_now = {
    "mood": 'earlier you saw the user looked %s. Ask them about that. ',
    "evesdrop": 'you heard the user say "%s" earlier. ask a follow up question'
}

class AI_Gemini(AI):
    
    memory = ""
    gemini = 0
    config=0
    model = cf.g('GEMINI_MODEL')
    model_slow = cf.g ('GEMINI_MODEL_SLOW')
    name = "Gemini"

    def __init__(self):
        AI.__init__(self)
        genai.configure(api_key=cf.g('GEMINI_API_KEY'))        
        app_desc = cf.g('BACKSTORY')
        self.gemini = genai.GenerativeModel(model_name=self.model,system_instruction=app_desc)     
        self.config = genai.types.GenerationConfig(
            max_output_tokens = 50,
            temperature = 1.0  # higher numbers for more creative responces
        )
        return

    def respond(self, user_input, canParaphrase=False):
        reply = ""
        file = ""
        
        this_model = self.model
        class_resp = AI.respond(self, user_input)  # will return either a response
#       The parent class handled the input.  
#       Unless told to paraphrase, return

        if class_resp:
            if class_resp == "return":
                return  # don't say anything
            elif class_resp == "goodbye": # allow the AI to say goodbye
                user_input =  "I have to go now, goodbye"
            elif class_resp[0] == '#':  # its a picture
                l = class_resp.split('#')
                file = PIL.Image.open(l[2])
                user_input = [file, l[1]]
            elif canParaphrase and not cf.g('SAVE_TOKENS'):
                user_input = "Paraphrase '"+class_resp+"'"
            else:
                return class_resp

        self.leds.thinking()
        try:
            reply = self.gemini.generate_content(user_input) #, generation_config=self.config)
            reply = str(reply.text.encode('ascii', 'ignore').decode("utf-8"))
        except Exception as e:
            reply = f"There was an error talking to Gemini: {str(e)}"

        self.leds.off()
        return reply

    #ON Startup
    def Hello(self):
        return f"!The user's name is {cf.g('USERNAMEP')}, say hello."
#             return cf.g('USERNAMEP')+" just arrivted after "+AI.PrettyDuration(self, datetime.now() - self.last_interaction) +", greet them."
#        else:
#              return self.respond("Hello!")

    # On Wake State return greeting
    def WakeMessage(self):
        resp = "!The user just called to you."
        return self.respond(resp)
        
    
    # From Sleep State return greeting
    def Greet(self):
          resp = "!The user just returned just returned after "+AI.PrettyDuration(self, datetime.now() - self.last_user_interaction) +", greet them."

 #       resp = AI.Greet(self)
             # and you haven't seen the user for  " + AI.PrettyDuration(datetime.now() - self.last_interaction) + ".  Greet them."
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


    def Close(self):
       AI.Close(self)
       return


    def get_emotion(self):
        return self.respond("in one word does user feel happy, sad, afraid or angry?")


if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')
    
    ai = AI_Gemini()
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
#    user_inp = "#Here is a picture of me#temp/capture_0_20240827201920388254.jpg"
#    print(ai.respond(user_inp))
#    while user_imp != "quit":
#        print("User: ", end="")
#        user_inp = input()
#        out = ai.respond(user_inp)
#        print(f'AI: {out}')

