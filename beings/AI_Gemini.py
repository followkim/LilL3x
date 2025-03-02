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

class AI_Gemini(AI):
    
    memory = ""
    gemini = 0
    config= 0
    model = cf.g('GEMINI_MODEL')
    model_slow = cf.g ('GEMINI_MODEL_SLOW')
    name = "Gemini"
    training = True
    has_vision = True

    def __init__(self):
        AI.__init__(self)
        genai.configure(api_key=cf.g('GEMINI_API_KEY'))
        system = f"{cf.g('BACKSTORY')}  {cf.g('INSTRUCTION')}"
        self.gemini = genai.GenerativeModel(model_name=self.model,system_instruction=[cf.g('BACKSTORY'), cf.g('INSTRUCTION')])
        self.config = genai.types.GenerationConfig(
#            max_output_tokens = 50,
            temperature = cf.g('TEMPERATURE')
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
            if class_resp in ( "return", "", "!"):
                return  "" # don't say anything
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

        self.face.thinking()
        try:
            reply = self.gemini.generate_content(user_input) #, generation_config=self.config)
            reply = str(reply.text.encode('ascii', 'ignore').decode("utf-8"))
        except Exception as e:
            reply = f"There was an error talking to Gemini: {str(e)}"

        self.face.off()
        return reply

    def Close(self):
       AI.Close(self)
       return

if __name__ == '__main__':

    from face import DummyFace

    import face
    global STATE
    STATE.ChangeState('Idle')

    ai = AI_Gemini()
    ai.face = DummyFace()
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_imp = "#Here is a picture of me#temp/capture_0_20240827201920388254.jpg"
#    print(ai.respond(user_inp))
    while user_imp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')

