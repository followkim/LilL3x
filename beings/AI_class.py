import os
import sys
import inspect
from pathlib import Path
from word2number import w2n
import requests
import re
from datetime import datetime, timedelta
import random
import threading
import socket
from subprocess import check_output

# import parent modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

print(f'Importing modules from {os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}')
from openface import ProcessOpenFace
from messages import Messages
from globals import STATE
from config import cf


class AI:
    last_user_interaction = datetime(2024, 8, 8)
    last_ai_interaction = datetime(2024, 8, 8)
    name = ""
    messages = Messages()
    memory = 0
    ears = 0
    eyes =0
    mouth = 0
    leds =0
    has_auth = False
    def __init__(self):
        print("AI_class:init()")
        self.last_user_interaction = datetime.now()
        self.last_ai_interaction = datetime.now()
        self.has_auth = True

    def SetBody(self, ears, eyes, mouth, leds):
        self.ears = ears
        self.eyes = eyes
        self.mouth = mouth
        self.leds = leds

    def respond(self, txt):
        if not txt:
            return False
        if re.search(r"^what time is it$", txt.lower()):# , flags-re.IGNORECASE):
            return "It's " + datetime.now().strftime("%l %M %p")

#        if re.search("^(simon says)* (say|repeat (after me|this))* (.*)$"):
#            (a, c, b, ret) = re.compile("^(simon says)* (say|repeat (after me|this))* (.*)$").match(txt).groups()
#            return ret

        if re.search(r"^say (.*)$", txt):
            (ret) = re.compile("^say (.*)$").match(txt).groups()
            return ret[0]

        if re.search(r"^who (are you|is this)$", txt):
            return f"I am {self.name}."

        if re.search(r"^what (day|date) is it\s*", txt.lower()):# , flags-re.IGNORECASE):
            return "It's " + datetime.now().strftime("%A, %B %d")

        if re.search(r"^what('s| is) (my|our|your|the) ip( address)*$", txt.lower()):
            ips = check_output(['hostname', '--all-ip-addresses'])
            return ips.split()[0].decode()

        if re.search(r"^max (idle|idol)$", txt.lower()): # , flags-re.IGNORECASE):
            self.last_user_interaction = self.last_user_interaction + timedelta(minutes=360)
            STATE.last_dt = STATE.last_dt + timedelta(minutes=360)

        if re.search(r"^(quit|exit|goodbye)$", txt.lower()): # , flags-re.IGNORECASE):
            STATE.ChangeState('Quit')
            return "goodbye"

        if re.search(r"(watch the house|(your|you're) in charge|hold down the fort)$", txt.lower()):
            ret = re.compile("^(.*)(watch the house|(your|you're) in charge|hold down the fort)$").match(txt).groups()
            STATE.ChangeState('Surveil')
            return False # allow child class to general own input

        if re.search(r"^(is (something|anything) moving|can you see movement|am i moving)$", txt.lower()):
            return self.YesNo(self.eyes.IsUserMoving(), "Yes",  "No, not that I can see")

        if re.search(r"^can you see me$", txt.lower()):
            return self.YesNo(self.LookForUser(), "Yes",  "No, I can't")

        if re.search(r"^is (the room|it) dark( in here)?$", txt.lower()):
            return self.YesNo(self.eyes.IsDark(), "Yes it is",  "No it isn't")
#
#        if (re.search(r"^take (a|my) (picture|photo|snapshot)( of (that|this|me|us))?$", txt.lower()) or
#                re.search(r"^(hey )?look at (this|that)$", txt.lower())):
#            pict = self.eyes.SendPicture()
#            if pict:
#                self.say("What is this a picture of?")
#                desc=self.listen()
#                return '#'+desc+'#'+pict
#            else:
#                return "Sorry, I couldn't take a picture"

        if re.search(r"^((can i )?talk|switch|let me (talk|speak)) to (.*)*$", txt.lower()):    # , flags-re.IGNORECASE):
            AI = txt.split()[-1]
            STATE.ChangeState('ChangeAI')
            newState = AI[0].upper() + AI[1:].lower()

            # NEED FIX
            if re.search(r".*gpt$", newState.lower()):
                STATE.data = "ChatGPT"
            elif re.search(r"^kind", newState.lower()):
                STATE.data = "Kindriod"
            else:
                STATE.data = newState
            return "Goodbye"  # have the AI say goodbye
           
        if re.search(r"^(set|switch|change) (your |the )?(voice|speech engine) to (.*)$", txt):
            (ret) = re.compile("^.* to (.*)$").match(txt).groups()

            # NEED FIX
            new_engine = ret[0]
            if re.search(r"(pie|pi) tts$", txt.lower()):
                new_engine = "pytts"
            elif re.search(r"g( )?tts$", txt.lower()):
                new_engine = "gTTS"
            elif re.search(r".*gpt$", txt.lower()):
                new_engine = "ChatGPT"
            elif re.search(r"(11|eleven) labs$", txt.lower()):
                new_engine = "elevenLabs"
            elif re.search(r"Amazon$", txt.lower()):
                new_engine = "amazon"
            else:
                new_engine = ret[0]

            if (self.mouth.SwitchEngine(new_engine)):
                return (f"Switched speech engine to {new_engine}")
            else:
                return (f"Couldn't switch to {new_engine}")

        return False # unable to match string, have child do it


#        if re.search(r"^(load|import) config (file|values)*$", txt.lower()): # , flags-re.IGNORECASE):
#            return(cf.Loadconfig, "Done", "I couldn't load the config file")
#
#        if re.search(r"^(save|write|export) config (file|values)$", txt.lower()): # , flags-re.IGNORECASE):
#            return(cf.Writeconfig, "Done", "I couldn't write the config file")
#
#        if re.search(r"^what is (.*) set to$", txt.lower()):
#            return self.RetrieveKey(txt)
#
#        if re.search(r"^set (.*) to (.*)$", txt.lower()):
#             return self.SetKey(txt)
        # perform Interactions (belo)
        # switch AIs
        # switch speech/listening engines
        # reinstall software
        # reboot



    def YesNo(self, test, yes, no):
        if test:
            return yes
        else:
            return no

    # end config helpers
    def AreYouSure(self):
        self.say("Are you sure?")        
        return self.listen() == "yes"
        #TODO: ask user at least twice if no yes/no

    def say(self, txt):
        last_ai_interaction = datetime.now()
        txt = self.StripActions(txt) # *sigh* remove actions
        ret = self.mouth.say(txt, self.leds)
        return ret

    def listen(self, beQuiet=False):
        resp = self.ears.listen(beQuiet=False, leds=self.leds)
        if resp and not beQuiet:
            last_user_interaction = datetime.now()
        return resp

    def Intruder(self):
        url = self.eyes.SendPicture()
        print(f"INTRUDER!!! {url}")
        #email URL
        return

    def LookForUser(self, duration=10):
        ret = self.eyes.CanISeeYou(duration)
        #print(f"LookForUser: {ret}")
        return ret

    def Think(self):
        self.leds.thinking()
        if cf.IsConfigDirty():
            cf.LoadConfig()
        # Process OpenFace
        # get opinions on photos or messages
        # machine learning
        self.leds.off()
        return

    def Interact(self, dice=False):
        secs = (datetime.now() - self.last_ai_interaction).seconds

        # too soon for an action (and action not forced)
        if not dice and secs < (cf.g('INTERACT_MIN')*60):
             return
        elif secs > (cf.g('INTERACT_MAX')*60):
            dice = 1

        #  You can specify the action-- used in respond()
        if not dice:
            #                            interactions per hour (ie 12)
            dice = random.randint(0, ((60*60)/cf.g('ACTIVE_IDLE_SLEEP')) / cf.g('INITIATE_ODDS'))   #TODO

        # Try initiate convo based on past interactions
        if dice == 1:
            print(f"Performing Interaction after {secs/60} minutes.")

            #if the user is talking, evesdrop, otherwise try to start a convo
            if not self.ears.CanIHearYou():
                return self.InitiateConvo()
#            if self.ears.PlayingMusic():
#                self.messages.SetMessage("music", something, datetime.now())

            else:
                print("Can't Interact: Talking heard.  Evesdropping instead.")
                heard = self.ears.Evesdrop()
                if heard:
                    self.messages.SetMessage("evesdrop", heard, datetime.now())
                return
        return

    def SetEvent(self, event):  # DOTO maek this generic.  Allow push into messages
        event_name = event['event_name']
        event_date = event['event_date']
        self.messages.SetMessage('event', event_name, event_date)
        return (f"OK, I'll remind you about {event_name} at {event_date}")


    def Close(self):
        return

    # A few time utilities - might wnat to move these into a seperate file
    def TimeOfDay(self):
        date_now = datetime.now()
        resp = ""
        # what time is it?  Is it morning?
        hour = int(datetime.now().strftime("%H"))
        if hour in range (5, 11): 
            resp =  "morning"
        elif hour in range (12, 17):
            resp =  "afternoon"
        elif hour in range (18, 20):
            resp =  "evening"
        elif hour in range (21, 23) or hour in range(0,5):
            resp =  "night"
        return resp
      
    def PrettyDuration(self, dtd):
        ret = ""
        years = dtd.days // 365
        months = (dtd.days-(years*365)) // 30
        days = (dtd.days - (years*365) - (months * 30)) % 30 
        hours =(dtd.seconds//(60*60)) % 60 
        minutes =((dtd.seconds//60)) % 60
        seconds =(dtd.seconds) % 60

        if years>1 :
            ret += str(years) + " years, "
        if years==1:
            ret += str(years) + " year, "

        if months>1 :
            ret += str(months) + " months, "
        if months==1:
            ret += str(months) + " month, "
        if days>1 :
            ret += str(days) + "  days, "
        if days==1:
            ret += str(days) + " day, "
        
        if days<1:
            if hours>1 :
                ret += str(hours) + " hours, "
            if hours==1:
                ret += str(hours) + " hour, "

            if minutes>1:
                ret += str(minutes) + " minutes, "
            if minutes==1:
                ret += str(minutes) + " minute, "
            if hours<1:

                if seconds>1:
                    ret += str(seconds) + " seconds, "
                if seconds==1 and not hours:
                    ret += str(seconds) + " seconds, "

        if ret:
            ret = " and ".join(ret[:-2].rsplit(", ", 1))
        return ret

    def StripActions(self, txt):
        exclude = False
        newStr = ""
        for s in txt:
            if s == '*':
                if exclude:
                    exclude = False
                else:
                    exclude = True
                continue    
            elif not exclude:
                newStr += s
        return newStr
'''
    # these helpers should probably go into config.py TODO
    def SetKey(self, txt):

         (key, val) = re.compile("^set (.*) to (.*)$").match(txt.lower()).groups()
         try:
            key = key.upper().replace(" ", "_")
            print(config.config_desc)
            if key in config.keys():
                if re.search(r"^int", config.config_desc[key]):
                   val = w2n.word_to_num(val)
                config[key] = val
                return f'Ok, I set {key} to {val}'
            else:
                raise KeyError
         except KeyError:
            return "I don't have an attribite called "+ key
         except Exception as e:
            return "I couldn't set "+ key + " to " + val + ".   " + str(e)

    def RetrieveKey(self, txt):
         key = re.compile("^what is (.*) set to$").match(txt.lower()).groups()[0].replace(" ", "_").upper()
         try:
            return f'{key} is set to {config[key]}'
         except KeyError:
               return f"I don't have an attribite called {key}."
         return f"Sorry, I couldn't get {key} from config data."
'''

if __name__ == '__main__':


    global STATE
    STATE.ChangeState('Idle')
 
    ai = AI()

    dtd = timedelta(days=65)
    ai.PrettyDuration(dtd)

    dtd = timedelta(seconds=65)
    ai.PrettyDuration(dtd)


    out = "hello"
    while out != "Goodbye":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')
'''
    ai.say("Hello!  ")
    imp = ai.listen()
    ai.say(f'You said {imp}')

    print(f"Can I see you? {ai.LookForUser()}")
    print(f'Evesdrop: {ai.Interact(2)}') # set evesdrop
    print(f'Return Message? {ai.Interact(2)}') # set evesdrop
    print(f'Evesdrop: {ai.Interact(2)}') # set evesdrop
    print(f'Return Evesdrop: {ai.Interact(3)}') # set evesdrop
    print(f'Init Convo: {ai.Interact(3)}') # set evesdrop



    ai.Interact(2) # shjould return evesdrop message
    ai.Interact(2) # evesdrop
    ai.Interact(3) # shjould return evesdrop message
    ai.Interact(3) # should init convo

'''
