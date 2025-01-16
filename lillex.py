#!/usr/bin/env python3
import welcome
import os
import sys
import re
import subprocess

os.chdir(f"{os.getenv('HOME')}/LilL3x/")
sys.path.append(f"{os.getenv('HOME')}/LilL3x/")

import inspect
from pathlib import Path
import logging
import threading
import time
from time import sleep
from datetime import datetime, timedelta
from multiprocessing import Process
import signal

# START LILL3X modules
from error_handling import *
InitLogFile()
from globals import STATE, SleepOn
import vosk_wake
import pico_wake
from config import cf

from listen_tools import SpeechRecognition_listener
from vosk_wake import Vosk_listener
from speech_tools import speech_generator
from camera_tools import Camera
from face import Face

currentdir = os.getcwd()

LogInfo("Importing AI...")
sys.path.insert(0, currentdir+'/beings/')
from AI_Dude import AI_Dude
from AI_Openai import *
from AI_Ollama import *
from AI_Kindriod import AI_Kindriod
from AI_Gemini import AI_Gemini
from AI_Claude import AI_Claude

sys.path.insert(0, currentdir+'/raspberryPi/')
from button import Button

sys.path.insert(0, currentdir)


class lill3x:

    ai = False
    ww = 0
    def __init__(self):

#        InitLogFile()  This is done above to capture log messages while loading externals
        LogInfo(f"Starting {GetHostname()}")
        # create the hardware objects

        try:
            self.mouth = speech_generator()
        except Exception as e:
            RaiseError(f"Init():Could not init speech generator. {e.args}")
            STATE.ChangeState('Quit')
            return # fatal

        try:
            self.eyes = Camera()
        except Exception as e:
            RaiseError(f"Init():Could not init camera. {e.args}")

        try:
            self.face = Face() # note this spawns two threads: animate and led threads
            self.face.SetViewControl(self.eyes.ShowView, self.eyes.EndShowView)
        except Exception as e:
            RaiseError(f"Init():Could not init Display. {e.args}")

        try:
            self.ears = eval(f"{cf.g('LISTEN_ENGINE')}_listener(self.face)")
#            self.ears = SpeechRecognition_listener()
        except Exception as e:
            RaiseError(f"Init():Could not init listener. {e.args}")
            STATE.ChangeState('Quit')
            return # fatal

        try:
            self.button = Button()
        except Exception as e:
            RaiseError(f"Init():Could not init Button. {e.args}")

        # get AI (depending on config)
        try:
            self.ai = eval(f"AI_{cf.g('AI_ENGINE')}()")
            self.ai.SetBody(self.ears, self.eyes, self.mouth, self.face)
        except Exception as e:
            RaiseError(f"Unable to create AI: {e.args}")
            STATE.ChangeState('Quit')
            return # fatal
        if not self.ai:
            RaiseError("Unable to create AI: init failed")
            STATE.ChangeState('Quit')
            return
        
        # THREADS
        cam_thread = threading.Thread(target=self.eyes.CameraLoopThread, daemon=True)
        cam_thread.name = f"{GetHostname()} CameraLoopThread"
        cam_thread.start()

#        self.ww = vosk_wake.vosk_wake(self.face)
        self.ww = eval(f"{cf.g('WAKE_WORD_ENGINE')}_wake.{cf.g('WAKE_WORD_ENGINE')}_wake(self.face)")
        ww_thread = threading.Thread(target=self.ww.ww_thread, daemon=True)
        ww_thread.name = f"{GetHostname()} WakeWordThread"
        ww_thread.start()
        
        button_thread = threading.Thread(target=self.button.ButtonThread, args=(self.mouth,), daemon=True)
        button_thread.name = f"{GetHostname()} ButtonThread"
        button_thread.start()

        config_thread = threading.Thread(target=cf.config_thread, daemon=True)
        config_thread.name = f"{GetHostname()} ConfigThread"
        config_thread.start()

        if '--restart' in sys.argv:
            STATE.ChangeState('ActiveIdle')
            try: self.last_ai_interaction = datetime.strptime(cf.g('LAST_INTERACTION'), cf.g('CONFIG_DT_FORMAT'))
            except:  pass
            LogInfo(f"Last Interaction:  {self.last_ai_interaction.strftime('%B %d, %Y %I:%M %p')}.")
        else:
            STATE.ChangeState('Hello')

    def Loop(self):
        LogInfo("Starting Main Loop")
        last_err = False  # we can ignore a single error... but if there are two in a row then quit.
        while not STATE.ShouldQuit():
            STATE.HWState(cf.g('DEBUG') or cf.g('SCREEN_DEBUG'))  # will only update every 10 secs
            if STATE.temp >= cf.g('CPU_MAX_TEMP'):
                if STATE.temp >= 80:
                    self.ai.say(f"I am {STATE.temp} degrees celcius, and that's too hot. Let me cool down and we'll try again.")
                    RaiseError(f"Heat error: {STATE.temp}.  Quitting.")
                    STATE.ChangeState('Quit') 
                else:
                    RaiseError(f"Temp Warning: {STATE.temp}") 
                    sleep(2)
            try:
                eval("self."+STATE.GetState()+"()")
                last_err = False
            except Exception as e:
                LogError(f"Loop(): {STATE.GetState()}: Uncaught Exception: {e.args}")
                if last_err: STATE.ChangeState('Quit')
                else: last_err = True

        # call the Quit function
        eval("self."+STATE.GetState()+"()")

    def ChangeAI(self):
        LogInfo(f"Changing AI to {STATE.data}.")
        self.SwitchAI(STATE.data)
        STATE.ChangeState('Hello')
        return True


    def SwitchAI(self, newAI):
        try:
            new_ai = eval(f"AI_{newAI}()")

        except Exception as e:
            LogError("Unable to create AI: {e.args}")
            self.ai.say(f"I wasn't able to switch to {newAI}.  {e.args}")
            return False

        if not new_ai.has_auth:
            LogError("Unable to create AI {newAI}: auth failed")
            self.ai.say(f"I wasn't able to switch to {newAI}.  Authorization error.")
            return False

        # were able to create the AI!
        self.ai.Close() # blocking, no threads
        self.ai = new_ai
        self.ai.SetBody(self.ears, self.eyes, self.mouth, self.face)
        cf.s('AI_ENGINE', newAI)
        return True

    def ChangeListener(self):
        LogInfo(f"Changing Listener to {STATE.data}.")
        self.SwitchListener(STATE.data)

    def SwitchListener(self, newListener):
        ears = None
        try:
            ears = eval(f"{newListener}_listener(self.face)")
        except Exception as e:
            LogError("SwitchListener():Could not init listener. " + e.args)
            return False

        # were able to create the listner
        self.ears.Close() # blocks, no threads
        self.ears = ears
        self.ai.ears = self.ears
        cf.s('LISTEN_ENGINE', newListener)
        STATE.ChangeState('Active')
        return True

    def EvalCode(self):
        LogDebug(f"EvalCode: {STATE.data}")
        for cmd in STATE.data:
            try:
                eval(cmd)
            except Exception as e:
                LogError(f"EvalCode failed.\n\tcmd:{cmd}\n\tErr: {e.args}")
        cf.WriteConfig()
        STATE.data = ""
        STATE.RevertState()

    # Hello: Give a greeting to the user:
    def Hello(self):
        self.ai.say(self.ai.Hello())
        STATE.ChangeState('Active')
        return

    # Wake: AI has just been summoned by user at any time.  Also the entry point into the loop
    def Wake(self):
        wp = self.ww.GetWakePhrase()
        if wp and not re.search(f"^((hey|ok|okay|so) )?{cf.c('AINAMEP', 'AINAME').lower()}$", wp.lower()):
            self.ai.say(self.ai.respond(wp))
        STATE.ChangeState('Active')
 
    # Active: User is present and activly talking to ai without need for wakeword
    #          AI can: listen and respond to user
    def Active(self):
        user_input = self.ai.listen()
        if user_input:
            self.ai.say(self.ai.respond(user_input))
        else:
            STATE.ChangeState('ActiveIdle')

    # ActiveIdle: User is present but not talking.   User needs to use wakeword or respond to an  inituation to activate ai
    #             AI can: initiate convo (based on evesdrop and get mood)
    def ActiveIdle(self):

        # if we've been in ActiveIdle state for a while with no interactions and can't see user go into Idle and leave the user alone
#        if self.ai.LastUserInteraction() > cf.g('ACTIVE_IDLE_TO')*60:

        if self.ai.IsIdle(): # not (cf.g('ACTIVE_IDLE_TO')*60)):  #hasn't seen the user in ACTIVE_IDLE_TO minutes, go to idle
            STATE.ChangeState('Idle')

        elif self.ai.CanInteract():
            thought = self.ai.Interact()    #returns text, but we want to update first
            if thought:
                self.ai.say(thought)
                STATE.ChangeState('Active')
            else: SleepOn(cf.g('ACTIVE_IDLE_SLEEP'))
        else: SleepOn(cf.g('ACTIVE_IDLE_SLEEP'))

    # Idle: User is not present.   User needs to be seen on camera, use wakeword,  or respond to "welcome back" to activate ai
    #       AI can: machine laining, check lights/sound
    def Idle(self):

        #TODO: Thinkign while activeIdle is different then thinkign while IdleIdle
        self.ai.Think()  # will need a flag that data should be saved for later
        
        if self.ai.CanInteract():        # can see user and not too soon
          self.ai.say(self.ai.Greet())
          STATE.ChangeState('Active')
        else:
            SleepOn(varf=self.ai.CanInteract, wakeOn=True)  # sleep until State change or seeing user

    # Sleep: User is not present.   User needs to use wakeword or respond to "welcome back" to activate ai
    #       AI can: machine learning, check lights/sound
    def SleepState(self):

        # user turned on the light-- goto acttive idle
        if not self.eyes.IsDark():
            if self.ai.IsIdle():
                STATE.ChangeState('Idle')
            else:
                STATE.ChangeState('ActiveIdle')  # will switch to Active Idle once user is seen
        else:
            CleanDirs(cf.g('TEMP_PATH'), 6)
            SleepOn(varf=self.eyes.IsDark, wakeOn=False)

    #User has asked Lil3x to watch the house.  Take pictures of any movement and send them RIGHT AWAY!
    # Will not leave state until wakeword heard.  (Eventually woudl be nice to be able to recognise user
    def Surveil(self):
        if STATE.StateDuration() > (cf.g('SURVEIL_WAIT')*60) and self.eyes.IsUserMoving():
            self.ai.say(self.ai.Intruder())
            user_input = self.ai.listen()
            if user_input:                                 # have to see if the user responds before going into active
                self.ai.say(self.ai.respond(user_input))
                STATE.ChangeState('Active')
            else:
                self.Sleep(cf.g('SURVEIL_LOOK')*60)  # don't send another notice for SURVEIL_LOOK minuntes
        else:
            SleepOn(varf=self.eyes.IsUserMoving, wakeOn=True)
        return

    def Quit(self):
       self.ww.Close()
       self.ai.Close()
       self.mouth.Close()
       self.ears.Close()
       self.eyes.Close()
       self.face.Close()
       cf.Close()
       self.WaitThreads()
       CloseLog()

    def Restart(self):
       self.Quit()
       python = sys.executable
       args = [sys.argv[0], "--restart"]
       cmd = [python] + args
       subprocess.Popen(cmd, start_new_session=True)


    def Reboot(self):
       self.Quit()
       os.system("sudo reboot")

    def WaitThreads(self):
       threads = threading.enumerate()
       numThreads = len(threads)
       while numThreads > 0:
           threads = threading.enumerate()
           numThreads = len(threads)
           for t in threads:
               if re.search(f"{GetHostname()}", t.name): LogInfo(f"T={len(threads)} Waiting on {t.name}.")
               else: numThreads = numThreads - 1
           sleep(2)

       

     # A version of sleep that will break out if the state changes by WakeWord.   Avoids long period of uninterruptable sleep.
    def Sleep(self, secs):
        global STATE
        curr_state = STATE.GetState()
        target_time = datetime.now() + timedelta(seconds=secs)
        sleep_for = min(cf.g('SLEEP_DURATION'), secs)
        while (datetime.now() < target_time) and STATE.CheckState(curr_state) and not (STATE.ShouldQuit() or  STATE.IsInteractive()):
            sleep(sleep_for)


## THREADING INFO
#os.chdir('/home/el3ktra/LilL3x/')
# Get the current working directory
CleanDirs("./temp", )

print(f"{GetHostname()} started at {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
l3x = lill3x()
l3x.Loop()
print(f"{GetHostname()} exited at {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
