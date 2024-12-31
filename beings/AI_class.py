import os
import sys
import inspect
from gpiozero import CPUTemperature
from pathlib import Path
from time import sleep
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

#from openface import ProcessOpenFace
from error_handling import *
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
    face = 0
    has_auth = False
    training = False


    def __init__(self):
        self.last_user_interaction = datetime.now()
        self.last_ai_interaction = datetime.now()
        self.has_auth = True

    def SetBody(self, ears, eyes, mouth, face):
        self.ears = ears
        self.eyes = eyes
        self.mouth = mouth
        self.face = face
        self.face.message(f"Hello, {cf.g('USERNAME')}")

    def respond(self, txt):
        if not txt:
            return False

        if re.search(r"^(what is|what(')?s) your temp(erature)?", txt.lower()):
            return f"I am running at {CPUTemperature().temperature} celcius."

        if re.search(r"^what time is it$", txt.lower()):
            return "It's " + datetime.now().strftime("%l %M %p")

#        if re.search("^(simon says)* (say|repeat (after me|this))* (.*)$"):
#            (a, c, b, ret) = re.compile("^(simon says)* (say|repeat (after me|this))* (.*)$").match(txt).groups()
#            return ret

        if re.search(r"^say (.*)$", txt):
            (ret) = re.compile("^say (.*)$").match(txt).groups()
            return ret[0]

        if re.search(r"^who (are you|is this)$", txt):
            return f"I am {self.name}."

        if re.search(r"^what (day|date) is it\s*", txt.lower()):
            return "It's " + datetime.now().strftime("%A, %B %d")

        if re.search(r"^what('s| is) (my|our|your|the) ip( address)?$", txt.lower()):
            ips = check_output(['hostname', '--all-ip-addresses'])
            self.face.message(ips.split()[0].decode())
            return "My IP address is " + ips.split()[0].decode()

        if re.search(r"^max (idle|idol)$", txt.lower()): 
            self.last_user_interaction = self.last_user_interaction + timedelta(minutes=360)
            STATE.last_dt = STATE.last_dt + timedelta(minutes=360)

        if re.search(r"^(quit|exit|goodbye)$", txt.lower()): 
            STATE.ChangeState('Quit')
            return "goodbye"

        if re.search(r"^(reboot|restart|reset)$", txt.lower()): 
            STATE.ChangeState('Restart')
            return "see you soon"

        if re.search(r"^update( yourself| your code| git)?$", txt.lower()):
            retStr = "I had an error trying to update.  Check my logs."
            f = cf.IsGitDirty()
            if f>0:
                retStr = f"I updated {f} files.  "
                if STATE.ShouldQuit(): retStr = retStr + "It looks like I need a restart.  See you soon!"
            elif f==0: retStr = "Looks like I am all up to date."
            return retStr

        if re.search(r"(watch the house|(your|you're) in charge|hold down the fort)", txt.lower()):
            STATE.ChangeState('Surveil')
            return False # allow child class to general own input

        if re.search(r"^(is (something|anything) moving|can you see movement|am i moving)$", txt.lower()):
            return self.YesNo(self.eyes.IsUserMoving(), "Yes",  "No, not that I can see")

        if re.search(r"^can you see me$", txt.lower()):
            return self.YesNo(self.LookForUser(5), "Yes",  "No, I can't")

        if re.search(r"^is (the room|it) dark( in here)?$", txt.lower()):
            return self.YesNo(self.eyes.IsDark(), "Yes it is",  "No it isn't")

        if re.search(r"^show (me|us) what you see$", txt.lower()):
            self.LookForUser(10)
            return "Here is what I see"

        # TODO: parse out picture description
        if (re.search(r"^take (a|my) (picture|photo|snapshot)( of (that|this|me|us))?$", txt.lower()) or
                re.search(r"^(hey )?look at (this|that)$", txt.lower())):
            path = self.TakePicture(cf.g('CAMERA_PICT_SEC'))
            if path:
                url  = self.eyes.UploadPicture(path)
                desc = f"This is a picture of me, {cf.g('USERNAME')}.  Describe and comment."
                return f'#{desc}#{path}#{url}'
            else:
                return "Sorry, I couldn't take a picture"

        if re.search(r"^((can i )?talk|switch|let me (talk|speak)) to (.*)*$", txt.lower()):    # , flags-re.IGNORECASE):
            AI = txt.split()[-1]
            STATE.ChangeState('ChangeAI')
            newState = AI[0].upper() + AI[1:].lower()

            # NEED FIX
            if re.search(r".*gpt$", newState.lower()):
                STATE.data = "ChatGPT"
            elif re.search(r"^kind", newState.lower()):
                STATE.data = "Kindriod"
            elif re.search(r"(gwen|quinn)", newState.lower()):
                STATE.data = "Qwen"
            elif re.search(r"(ele(k|c)tra|alexa)", newState.lower()):
                STATE.data = "El3ktra"
            else:
                STATE.data = newState
            return "Goodbye"  # have the AI say goodbye
           
#        if re.search(r"^(set|switch|change) (your |the )?(model)$", txt):
#            self.say("Please type in the new model to use:")
#            self.model = input()
#            return f"Switched model to {self.model}."

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
            elif re.search(r"amazon$", txt.lower()):
                new_engine = "amazon"
            else:
                new_engine = ret[0]

            if (self.mouth.SwitchEngine(new_engine)):
                cf.s('SPEECH_ENGINE', new_engine)
                return (f"Switched speech engine to {new_engine}")
            else:
                return (f"Couldn't switch to {new_engine}")



        if re.search(r"^((re)?load|import) config( file)?$", txt.lower()): # , flags-re.IGNORECASE):
            return(self.YesNo(cf.LoadConfig(), "Configuration variables updated.", "I couldn't load the config file"))

        if re.search(r"^(save|write|export) config( file)?$", txt.lower()): # , flags-re.IGNORECASE):
            return(self.YesNo(cf.WriteConfig(), "Configuration variables saved.", "I couldn't write the config file"))

        if re.search(r"^what is (the |your )?(.*) set to$", txt.lower()):
            (x, key) = re.compile("^what is (the |your )?(.*) set to$").match(txt).groups()
            key = key.upper().replace(' ', '_') 
            val = cf.g(key)
            if val == False:
                return f"I don't seem to have an attribute {key}."
            else:
                return f"{key} is set to {val}."

        #TODO cuases error, needs fix
        if re.search(r"^set (the |your )?(.*) to (.*)$", txt.lower()):
            (x, key, val) = re.compile("^set (the |your )?(.*) to (.*)$").match(txt).groups()
            key = key.upper().replace(' ', '_') 
            # check that key exsosts:
            if not cf.g(key):
                return f"I don't seem to have an attribute {key}."
            else:
                cf.s(key, val)
                return f"{key} is set to {cf.g(key)}."
#
#        if re.search(r"^set (.*) to (.*)$", txt.lower()):
#             return self.SetKey(txt)
        # perform Interactions (belo)
        # switch speech/listening enginespicture
        # reinstall software
        # reboot

        return False # unable to match string, have child do it


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

    def say(self, txt, asyn=False):
        self.last_ai_interaction = datetime.now()
        txt = self.StripActions(txt) # *sigh* remove actions
        ret = self.mouth.say(txt, self.face, asyn=asyn)
        return ret

    def listen(self, beQuiet=False):
        resp = self.ears.listen(face=self.face, beQuiet=beQuiet)
        resp = resp.replace('Alexa', 'El3ktra')
        if resp and not beQuiet:
            self.last_user_interaction = datetime.now()
        return resp

    def TrainData(self, user_input, reply):
        if self.training:
            filename = "training/AI_"+self.name + "_trn.dat"
            f = open(filename, 'a')
            f.write(user_input + "|" + reply.strip("\n") + "\n")
            f.close()

    def Intruder(self):
        url = self.eyes.SendPicture()
        LogConvo(f"INTRUDER!!! {url}")
        #email URL
        return

    def LookForUser(self, duration=0):
        if duration:
            self.face.looking()
            if self.WaitWIS(duration): sleep(duration)  # allow the user to admire the view
            self.face.off()
        return self.eyes.CanISeeYou()

    def TakePicture(self, duration=0):

        # wait for WIS file, then show the view to get teh user ready
        if duration: 
            self.face.looking()
            if self.WaitWIS(duration): sleep(duration)

        path = self.eyes.TakePicture()  # will shutter sound
        if path and duration:
            #show the picture TODO: this just shows the view
            sleep(duration)
        if duration: self.face.off()
        return path

    def WaitWIS(self, duration):
        # wait for the view to be shown
        end = datetime.now() + timedelta(seconds=duration)
        while not os.path.exists(cf.g('WIS_FILE')) and end>datetime.now(): sleep(0.1)
        return os.path.exists(cf.g('WIS_FILE'))

    def Think(self):
#        self.face.thinking()
#        if cf.IsConfigDirty():
#            cf.LoadConfig()
        # Process OpenFace
        # get opinions on photos or messages
        # machine learning
#        self.face.off()
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
            self.face.thinking()
            LogInfo(f"Performing Interaction after {secs/60} minutes.")
            
            #if self. the user is talking, evesdrop, otherwise try to start a convo
            if not self.ears.CanIHearYou():
                return(self.InitiateConvo(topic=self.eyes.GetEmotion()))
#            if self.ears.PlayingMusic():
#                self.messages.SetMessage("music", something, datetime.now())

            else:
                LogInfo("Can't Interact: Talking heard.  Evesdropping instead.")
                heard = self.ears.Evesdrop()
                if heard:
                    self.messages.SetMessage("evesdrop", heard, datetime.now())
            self.face.off()
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
        minutes =(dtd.seconds//60) % 60
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
        newStr = str(newStr.encode('ascii', 'ignore').decode("utf-8"))
        return newStr

if __name__ == '__main__':


    global STATE
    STATE.ChangeState('Idle')
 
    ai = AI()

    dtd = timedelta(days=65)
    ai.PrettyDuration(dtd)

    dtd = timedelta(seconds=65)
    ai.PrettyDuration(dtd)


    user_inp = "hello"
    while user_inp != "quit":
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
