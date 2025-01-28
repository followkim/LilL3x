import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import anthropic
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

class AI_Claude(AI):

    claude = 0
    config=0
    model = cf.g('CLAUDE_MODEL')
    model_slow = cf.g ('CLAUDE_MODEL_SLOW')
    name = "Claude"
    training = True
    has_vision = True
    def __init__(self):
        AI.__init__(self)


        self.claude =  anthropic.Anthropic(api_key=cf.g('CLAUDE_API_KEY'))

#        self.Claude = genai.GenerativeModel(model_name=self.model,system_instruction=app_desc)     
#        self.config = genai.types.GenerationConfig(
#            max_output_tokens = 50,
#            temperature = 1.0  # higher numbers for more creative responces
#        )
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

        self.face.thinking()
        try:
            message = self.claude.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=cf.g('TEMPERATURE'),
                system=f"You are a supportive friend to the user.  Your name is {cf.g('AINAMEP')}.  Provide converstaion and support.",
                messages=[{"role": "user", "content": [{"type": "text","text": user_input}]}]
            )
            reply = message.content[0].text
        except Exception as e:
            reply = f"There was an error talking to Claude: {str(e)}"

        self.face.off()
        return reply

    def Close(self):
       AI.Close(self)  # prints memory
       return

if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')
    from face import DummyFace
    user_inp = ""    
    ai = AI_Claude()
    ai.face = DummyFace()
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
#    user_inp = "#Here is a picture of me#temp/capture_0_20240827201920388254.jpg"
#    print(ai.respond(user_inp))
    while user_inp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')

