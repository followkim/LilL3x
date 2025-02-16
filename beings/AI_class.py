import os
import sys
import inspect
from pathlib import Path
from time import sleep
import requests
import re
import math
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
    ears = 0
    eyes =0

    mouth = 0
    face = 0
    has_auth = False
    training = False
    has_vision = False

    def __init__(self):
        self.last_ai_interaction = datetime.now()
        self.last_user_interaction = self.last_ai_interaction
        self.has_auth = True

    def SetBody(self, ears, eyes, mouth, face):
        self.ears = ears
        self.eyes = eyes
        self.mouth = mouth
        self.face = face
        self.face.message(self.name)

    def respond(self, txt):
        if not txt:
            return False

        
        search_txt_p = txt.lower().strip()
        search_txt = re.sub(r'[^\w\s]', '', search_txt_p)

        if re.search(r"^(not now|shut up|be quiet|go away|later|stop)$", search_txt.lower()):
            STATE.ChangeState('ActiveIdle')
            return f"ok"

        if re.search(r"^(what is|what(')?s) your temp(erature)?", search_txt.lower()):
            return f"I am running at {STATE.temp} celcius."

        if re.search(r"^what time is it$", search_txt.lower()):
            return "It's " + datetime.now().strftime("%l %M %p")

#        if re.search("^(simon says)* (say|repeat (after me|this))* (.*)$"):
#            (a, c, b, ret) = re.compile("^(simon says)* (say|repeat (after me|this))* (.*)$").match(txt.lower()).groups()
#            return ret

        if re.search(r"^say (.*)$", search_txt):
            (ret) = re.compile("^say (.*)$").match(search_txt).groups()
            return ret[0]

        if re.search(r"^who (are you|is this)$", search_txt):
            return f"I am {self.name}."

        if re.search(r"^what (day|date) is it\s*", search_txt):
            return "It's " + datetime.now().strftime("%A, %B %d")

        if re.search(r"^what((')?s| is) (my|our|your|the) ip( address)?$", search_txt):
            ips = check_output(['hostname', '--all-ip-addresses'])
            self.face.message(ips.split()[0].decode())
            return "My IP address is " + ips.split()[0].decode()

        if re.search(r"(watch the house|(your|you're) in charge|hold down the fort)", search_txt):
            STATE.ChangeState('Surveil')
#            return f"!{self.GetString('SURVEIL_STR').format(cf.g('USERNAME'))}"
            return False # let AI handle user_input


        if re.search(r"^(quit|exit|shut( )?down)$", search_txt): 
            STATE.ChangeState('Quit')
            return "~see you later"

        if re.search(r"^(reboot|restart|reset)(.)?$", search_txt): 
            STATE.ChangeState('Restart')
            return "~see you soon"

        if re.search(r"^upload (a| the |your )?log( )?(file)?(s)?$", search_txt): 
            return self.YesNo(UploadLog(), "I uploaded my log file", "I couldn't upload my log file")

        if re.search(r"^update( yourself| your code| git)?$", search_txt):
            retStr = "I had an error trying to update.  Check my logs."
            f = cf.CheckGit()
            if f>0:
                retStr = f"I updated {f} files.  "
                if STATE.ShouldQuit(): retStr = retStr + "It looks like I need a restart.  See you soon!"
            elif f==0: retStr = "Looks like I am all up to date."
            return retStr


        if re.search(r"(show|dump|output|print)( your)? (running |current |active )?threads", search_txt):
            return f"I have {ShowThreads()} running, check the logs for a list."

        if re.search(r"^(is (something|anything) moving|can you see movement|am i moving)$", search_txt):
            self.LookForUser(cf.g('CAMERA_PICT_SEC'))
            return self.YesNo(self.eyes.IsUserMoving(), "Yes, I see movement",  "No, I can't see any movement")

        if re.search(r"^can you see me$", search_txt):
            return self.YesNo(self.LookForUser(cf.g('CAMERA_PICT_SEC')), "Yes, I can see you!",  "No, I can't see you")

        if re.search(r"^is (the room|it) dark( in here)?$", search_txt):
            return self.YesNo(self.eyes.IsDark(), "~Yes it is dark in here",  "~No it isn't dark in here")

        if re.search(r"^show (me|us) what you see$", search_txt):
            self.LookForUser(10)
            return "~Here is what I see through my camera"

        # TODO: parse out picture description
        if self.has_vision and not self.tools and (re.search(r"(^|, |. |so |and )(get|take|snap) (a |my|our )(look|picture|photo|snapshot)( (at|of) (.*))?", search_txt_p) or
                re.search(r"^(hey )?look at (.*)$", search_txt)):
            '''
            m = re.search(r"^take (a |my|our )(look|picture|photo|snapshot)( (at|of) (.*))?$", search_txt)
            if not m: m2 = re.search(r"^(hey )?look at (.*)$", search_txt)

            selfie=False
            if m:
                if m[5]: desc = f"{self.GetString('CAMERA_STR').format('and '+ str(m[5]))}"
                if m[1] in ('my', 'our') or m[5] in ('me', 'us'): selfie = True
            elif m2: desc = f"{self.GetString('CAMERA_STR').format('and '+str(m2[2]))}"
            else: desc = f"{self.GetString('CAMERA_STR').format(cf.g('USERNAME'))}"
            '''
            desc = cf.g('CAMERA_STR')
            selfie = False
            path = self.TakePicture(cf.g('CAMERA_PICT_SEC'), selfie=selfie)

            if path:
                url  = self.eyes.UploadPicture(path)
                return f'#{desc}#{path}#{url}'
            else:
                return "Sorry, I couldn't take a picture"

        if re.search(r"^((can i )?talk|switch|let me (talk|speak)) to (.*)*$", search_txt):    # , flags-re.IGNORECASE):
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
            elif re.search(r"(deep seek)", newState.lower()):
                STATE.data = "Deepseek"
            elif re.search(r"(ele(k|c)tra|alexa)", newState.lower()):
                STATE.data = "El3ktra"
            else:
                STATE.data = newState
            return f"Sure, I'll switch to {STATE.data}"  # have the AI say goodbye

#        if re.search(r"^(set|switch|change) (your |the )?(model)$", txt):
#            self.say("Please type in the new model to use:")
#            self.model = input()
#            return f"Switched model to {self.model}."

        if re.search(r"^(set|switch|change) (your |the )?(voice|speech engine) to (.*)$", search_txt):
            (ret) = re.compile("^.* to (.*)$").match(search_txt).groups()

            # NEED FIX
            new_engine = ret[0]
            if re.search(r"(pie|pi)( )?tts$", search_txt):
                new_engine = "pytts"
            elif re.search(r"g( )?tts$", search_txt):
                new_engine = "gTTS"
            elif re.search(r".*gpt$", search_txt):
                new_engine = "ChatGPT"
            elif re.search(r"(11|eleven) labs$", search_txt):
                new_engine = "elevenLabs"
            elif re.search(r"amazon$", search_txt):
                new_engine = "amazon"
            else:
                new_engine = ret[0]

            if (self.mouth.SwitchEngine(new_engine)):
                cf.w('SPEECH_ENGINE', new_engine)
                return (f"Switched speech engine to {new_engine}")
            else:
                return (f"Couldn't switch to {new_engine}")

        if re.search(r"^(set|switch|change) (your |the )?listen(ing|er)?( engine)? to (.*)$", search_txt):
            engine  = False

            if re.search(r"speech( )?recogni(tion|ize)$", search_txt):
                engine = "SpeechRecognition"
            elif re.search(r"vos(c|k|t)$", search_txt):
                engine = 'Vosk'
            if engine:
                STATE.ChangeState('ChangeListener')
                STATE.data = engine
                return f"Sure, I'll switch the listener to {engine}."
            else: return f"I can't seen to find a listening engine called {txt.split()[-1]}"

#        if re.search(r"^turn( off| down |up)? the (light|led)(s?)( down| off|up)?$", search_txt):
#            g = re.compile("^turn( off| down)? the (light|led)(s?)( down| off)?").match(search_txt)
#            return "Here is what I see"

        if re.search(r"^((re)?load|import) (the |your )?config( file)?$", search_txt): # , flags-re.IGNORECASE):
            return(self.YesNo(cf.LoadConfig(), "Configuration variables updated.", "I couldn't load the config file"))

        if re.search(r"^(save|write|export) (the |your )?config( file)?$", search_txt): # , flags-re.IGNORECASE):
            return(self.YesNo(cf.WriteConfig(), "Configuration variables saved.", "I couldn't write the config file"))

        if re.search(r"^what is ((the|your) )?(.+) set to$", search_txt):
            (x, y, key) = re.compile("^what is( (the|your))? (.+) set to$").match(search_txt).groups()
            key = key.upper().replace(' ', '_') 
            val = cf.g(key)
            if val == False:
                return f"I don't seem to have an attribute {key}."
            else:
                return f"{key} is set to {val}."

        #TODO cuases error, needs fix
        if re.search(r"^(set|change|update) (the |your )?(.+) to (.+)$", search_txt):
            (x, xx, key, val) = re.compile("^(set|change|update) (the |your )?(.+) to (.+)$").match(search_txt).groups()
            key = key.upper().replace(' ', '_') 
            # check that key exsosts:
            if not cf.g(key):
                return f"I don't seem to have an attribute {key}."
            else:
                cf.s(key, val)
                return f"{key} is set to {cf.g(key)}."
#
#        if re.search(r"^set (.*) to (.*)$", search_txt):
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
        resp = self.ears.listen(beQuiet=beQuiet)
        regex = re.compile(f"\\b{cf.c(cf.c('WAKE_WORD_REGEX', 'AINAMEP'), 'AINAME')}\\b")
        resp = re.sub(regex,  cf.g('AINAMEP'), resp)
        if resp and not beQuiet:
            self.last_user_interaction = datetime.now()
        return resp
    def TrainData(self, user_input, reply):
        if self.training:
            reply = self.StripActions(reply).strip('\n')+"\n"  # can't include '\n' in {}
            filename = "training/AI_"+self.name + "_trn.dat"
            f = open(filename, 'a')
            f.write(f"{datetime.now().strftime('%y-%m-%d %H:%M:%S')}|{user_input}|{reply}")
            f.close()

    def Intruder(self):
        url = self.eyes.SendPicture()
        LogConvo(f"{cf.g('AINAME')}: INTRUDER!!! {url}")
        #email URL
        return

    def CanIHearYou(self, duration=cf.g('AMBIENT')):
        start = datetime.now()
        avg = [STATE.volume]
        quiet = self.ears.GetQuiet()
        self.face.listening(cf.g('SHOW_USER_CHECK'))
        newVol = STATE.volume - quiet
        while (datetime.now()-start).seconds<duration:  # floor the volume for the meter
            if STATE.volume != newVol:
                avg.append(STATE.volume)  # don't accidently append the floored one
                if cf.g('SHOW_USER_CHECK'):
                    newVol = STATE.volume-quiet
                    STATE.volume = newVol

        self.face.off(cf.g('SHOW_USER_CHECK'))

        vol = round(sum(avg) / len(avg))
        LogDebug(f"CanIHearYou:vol={vol} > q={round(quiet)}: {vol > quiet}")
        return vol and vol > quiet


    def LookForUser(self, duration=0):
        if duration or cf.g('SHOW_USER_CHECK'):
            if not duration: duration = cf.g('LOOK_SECS_TO_DEFAULT')
            self.face.looking()
            if self.WaitWIS(duration): sleep(cf.g('CAMERA_PICT_SEC'))  # WaitWIS blocks until wis fuke and sleep allows the user to admire the view
            self.face.off()
        return self.eyes.CanISeeYou()

    def TakePicture(self, duration=0, selfie=False):

        # wait for WIS file, then show the view to get teh user ready
        if duration>0:
            self.face.looking()
            if self.WaitWIS():
                sleep(duration)  # second sleep allows the user to see the camera

        if selfie: path = self.eyes.TakePortrait(beQuiet=(duration==0))  # will shutter sound if duration
        else: path = self.eyes.TakePicture(beQuiet=(duration==0))  # will shutter sound if duration
#        if path: sleep(duration)    #pause to show the picture (if duration==0 no sleep)
        return path

    def WaitWIS(self, duration=5):
        # wait for the view to be shown
        end = datetime.now() + timedelta(seconds=duration)
        while not os.path.exists(cf.g('WIS_FILE')) and end>datetime.now(): sleep(0.1)
        return os.path.exists(cf.g('WIS_FILE'))

    def Think(self):

        return

    def IsIdle(self):
         return not self.LookForUser() and self.LastInteraction() > ((cf.g('ACTIVE_IDLE_TO')*60) & 0xffffffff)


    def CanInteract(self):
        if not ('INITIATE_ODDS') or not self.LookForUser() or self.CanIHearYou(): return False
        secs = self.LastAIInteraction()

        # too soon for an action (and action not forced)
        if secs > 0 and secs < (cf.g('INTERACT_MIN')*60):
            return False
        elif secs > (cf.g('INTERACT_MAX')*60):
            return True
        else: return False

    def Interact(self, dice=False):

        if not dice:
            if self.LastAIInteraction() > (cf.g('INTERACT_MAX')*60): dice = 1
        # if could interact: calculate random.  interactions per hour (ie 12) / initiate odds
        else: dice = random.randint(0, round(((60*60)/cf.g('ACTIVE_IDLE_SLEEP')) / cf.g('INITIATE_ODDS')))

        # If we hit the jackpot, interact
        if dice == 1:
            LogInfo(f"Performing Interaction after {round(self.LastUserInteraction()/60)} minutes.")
            return(self.InitiateConvo(mood=self.eyes.GetEmotion()))
        else: return ""

    def LastInteraction(self):
        if cf.g('IDLE_ON_CAMERA'): return min(self.eyes.LastSeen(), self.LastUserInteraction())
        else: return self.LastUserInteraction()

    def LastUserInteraction(self):
        return (datetime.now()-self.last_user_interaction).seconds

    def LastAIInteraction(self):
        return (datetime.now()-self.last_ai_interaction).seconds

    def SetEvent(self, event):  # DOTO maek this generic.  Allow push into messages
        event_name = event['event_name']
        event_date = event['event_date']
        self.messages.SetMessage('event', event_name, event_date)
        return (f"OK, I'll remind you about {event_name} at {event_date}")


    def Close(self):
        cf.s('LAST_INTERACTION', self.last_ai_interaction.strftime(cf.g('CONFIG_DT_FORMAT')))
        return

    # Default responses uses in AIs not designed to take demands. 

    # From Idle State return greeting when user seen
    def Greet(self):
          if (self.LastAIInteraction() / 3600) > 6:  # haven't talked to the user in more then 6 hours
              self.respond(f"Good {self.TimeOfDay()}!  It's been a few hours.")
          else: return self.InitiateConvo()

    def InitiateConvo(self, mood=""):
        if mood: return self.respond(f"I feel {mood} right now.")
        elif self.has_vision and random.randint(0, 4) == 1:
            path = self.TakePicture(0)
            if path:
                url  = self.eyes.UploadPicture(path)
                desc = f"Here is a picture of what you can see"
                return self.respond(f'#!{desc}#{path}#{url}') # force async

        return self.respond(f"Good {self.TimeOfDay()}")


    def Hello(self):
        return self.respond(f"Hello {cf.g('AINAME')}")

    def WakeMessage(self):
        resp = f"Hey {cf.g('AINAME')}"
        return self.respond(resp)

    # A few time utilities - might wnat to move these into a seperate file
    def TimeOfDay(self):
        date_now = datetime.now()
        resp = ""
        # what time is it?  Is it morning?
        hour = int(datetime.now().strftime("%H"))
        if hour in range (5, 12): 
            resp =  "morning"
        elif hour in range (12, 18):
            resp =  "afternoon"
        elif hour in range (18, 21):
            resp =  "evening"
        elif hour in range (21, 24) or hour in range(0,5):
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
        newStr = newStr.replace(cf.g('AINAME'  ), cf.c('AINAMEP',   'AINAME'  ))
        newStr = newStr.replace(cf.g('USERNAME'), cf.c('USERNAMEP', 'USERNAME'))
        newStr = newStr.replace(cf.g('USERNAME'), cf.c('USERNAMEP', 'USERNAME'))
#        newStr = newStr.replace('"', '')  # remove quotes
#        newStr = newStr.replace("'", '')
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
        out = ai.respond(ai.StripActions(user_inp))
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
