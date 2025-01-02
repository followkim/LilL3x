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
from gpiozero import CPUTemperature

# START LILL3X modules
from error_handling import *
InitLogFile()
from globals import STATE
import vosk_wake
import pico_wake
from config import cf

from speech_tools import speech_generator
from listen_tools import speech_listener
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

# how many seconds we should sleep in each state.
 #Note that sleeping still allows for WakeWord but higher values will cause less interaction and checks.
sleep_secs = {
    'ActiveIdle': cf.g('ACTIVE_IDLE_SLEEP'),
    'Idle': cf.g('IDLE_SLEEP'),
    'SleepState': cf.g('SLEEP_SLEEP')
}

# How long we stay in each state.
# State changes resets value.  For example, it takes 1 hour and 31 minutes to get into sleep
timeout_secs = {
    'ActiveIdle':cf.g('ACTIVE_IDLE_TO')*60,
    'Idle': cf.g('IDLE_TO')*60
}


class lill3x:

    ai = False
    ww = 0
    def __init__(self):

#        InitLogFile()  This is done above to capture log messages while loading externals
        LogInfo("Starting LilL3x")        
        # create the hardware objects
  
        try:
            self.mouth = speech_generator()
        except Exception as e:
            RaiseError("Init():Could not init speech generator. " + str(e))
            STATE.ChangeState('Quit')
            return # fatal

        try:
            self.ears = speech_listener()
        except Exception as e:
            RaiseError("Init():Could not init listener. " + str(e))
            STATE.ChangeState('Quit')
            return # fatal

        try:
            self.eyes = Camera()
        except Exception as e:
            RaiseError("Init():Could not init camera. " + str(e))

        try:
            self.face = Face() # note this spawns two threads: animate and led threads
            self.face.SetViewControl(self.eyes.ShowView, self.eyes.EndShowView)
        except Exception as e:
            RaiseError("Init():Could not init Display. " + str(e))

        try:
            self.button = Button() 
        except Exception as e:
            RaiseError("Init():Could not init Button. " + str(e))

        # get AI (depending on config)
        try:
            self.ai = eval("AI_"+cf.g('AI_ENGINE')+"()")
            self.ai.SetBody(self.ears, self.eyes, self.mouth, self.face)
        except Exception as e:
            RaiseError("Unable to create AI: "+ str(e))
            STATE.ChangeState('Quit')
            return # fatal
        if not self.ai:
            RaiseError("Unable to create AI: init failed")
            STATE.ChangeState('Quit')
            return
        
        # THREADS
        cam_thread = threading.Thread(target=self.eyes.CameraLoopThread, daemon=True)
        cam_thread.name = f"LilL3x CameraLoopThread"
        cam_thread.start()

#        self.ww = vosk_wake.vosk_wake(self.face)
        self.ww = eval(f"{cf.g('WAKE_WORD_ENGINE')}_wake.{cf.g('WAKE_WORD_ENGINE')}_wake(self.face)")
        ww_thread = threading.Thread(target=self.ww.ww_thread, daemon=True)
        ww_thread.name = f"LilL3x WakeWordThread"
        ww_thread.start()
        
        button_thread = threading.Thread(target=self.button.ButtonThread, args=(self.mouth,), daemon=True)
        button_thread.name = f"LilL3x ButtonThread"
        button_thread.start()

        config_thread = threading.Thread(target=cf.config_thread, daemon=True)
        config_thread.name = f"LilL3x ConfigThread"
        config_thread.start()

        if '--restart' in sys.argv: STATE.ChangeState('ActiveIdle')
        else:
            self.mouth.Hello()
            STATE.ChangeState('Hello')

    def Loop(self):
        LogInfo("Starting Main Loop")
        last_err = False  # we can ignore a single error... but if there are two in a row then quit.
        while not STATE.ShouldQuit():
            temp = CPUTemperature().temperature
            if temp >= cf.g('CPU_MAX_TEMP'):
                if temp >= 80:
                    self.ai.say(f"I am {temp} degrees celcius, and that's too hot. Let me cool down and we'll try again.")
                    RaiseError(f"Heat error: {temp}.  Quitting.")
                    STATE.ChangeState('Quit') 
                else:
                    RaiseError(f"Temp Warning: {temp}") 
                    sleep(2)
            try:
                eval("self."+STATE.GetState()+"()")
                last_err = False
            except Exception as e:
                LogError(f"Loop(): {STATE.GetState()}: Uncaught Exception: {str(e)}")
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
            LogError("Unable to create AI: {str(e)}") 
            self.ai.say(f"I wasn't able to switch to {newAI}.  {str(e)}")
            return False

        if not new_ai.has_auth:
            LogError("Unable to create AI {newAI}: auth failed")
            self.ai.say(f"I wasn't able to switch to {newAI}.  Authorization error.")
            return False

        # were able to create the AI!
        self.ai.Close()
        self.ai = new_ai
        self.ai.SetBody(self.ears, self.eyes, self.mouth, self.face)
        cf.s('AI_ENGINE', newAI)
        return True

    def EvalCode(self):
        LogDebug(f"EvalCode: {STATE.data}")
        for cmd in STATE.data:
            try:
                eval(cmd)
            except Exception as e:
                LogError(f"EvalCode failed.\n\tcmd:{cmd}\n\tErr: {str(e)}")
        STATE.data = ""
        STATE.RevertState()

    # Hello: Give a greeting to the user:
    def Hello(self):
        self.ears.clear()
        self.ai.say(self.ai.Hello())
        STATE.ChangeState('Active')
        return

    # Wake: AI has just been summoned by user at any time.  Also the entry point into the loop
    def Wake(self):
        wp = self.ww.GetWakePhrase()
        if wp and not re.search(f"^((hey|ok|okay|so) )?{cf.g('AINAME').lower()}$", wp.lower()):
            self.ai.say(self.ai.respond(wp))
        STATE.ChangeState('Active')
 
    # Active: User is present and activly talking to ai without need for wakeword
    #          AI can: listen and respond to user
    def Active(self):
        user_input = self.ai.listen()
        if user_input:
            update_thread = threading.Thread(target=self.ears.update)
            update_thread.start()
            self.ai.say(self.ai.respond(user_input))
        else:
            STATE.ChangeState('ActiveIdle')

    # ActiveIdle: User is present but not talking.   User needs to use wakeword or respond to an  inituation to activate ai
    #             AI can: initiate convo (based on evesdrop and get mood)
    def ActiveIdle(self):

        # if we've been in ActiveIdle state for a while with no interactions and can't see user go into Idle and leave the user alone
        if STATE.StateDuration() > timeout_secs.get(STATE.GetState(), 0):
            STATE.ChangeState('Idle')

        if self.eyes.IsDark():
             STATE.ChangeState('SleepState')
             self.face.off()
        elif STATE.CheckState('ActiveIdle') and not self.ww.is_speaking and self.ai.LookForUser():
            thought = self.ai.Interact()  
            if thought:
                self.ears.update()  # get ambient noise
                self.ai.say(thought)
                user_input = self.ai.listen()
                if user_input:
                    self.ai.say(self.ai.respond(user_input))
                    if STATE.CheckState('ActiveIdle'):
                        STATE.ChangeState('Active')

        self.Sleep(sleep_secs.get(STATE.GetState(), 0))

    # Idle: User is not present.   User needs to be seen on camera, use wakeword,  or respond to "welcome back" to activate ai
    #       AI can: machine laining, check lights/sound
    def Idle(self):

        #TODO: Thinkign while activeIdle is different then thinkign while IdleIdle
        self.ai.Think()  # will need a flag that data should be saved for later

#        if STATE.StateDuration() > timeout_secs[STATE.GetState()]:
        if self.eyes.IsDark():
            STATE.ChangeState('SleepState')
            self.face.off()
        # Check for the user
        else:
            is_user_there = self.ai.LookForUser()
            if is_user_there:
                self.ai.say(self.ai.Greet())
                user_input = self.ai.listen()
                if user_input:
                    self.ai.say(self.ai.respond(user_input))
                    STATE.ChangeState('Active')
                else: STATE.ChangeState('ActiveIdle')
            else:
                self.Sleep(sleep_secs.get(STATE.GetState(), 0))

    # Sleep: User is not present.   User needs to use wakeword or respond to "welcome back" to activate ai
    #       AI can: machine learning, check lights/sound
    def SleepState(self):

        # user turned on the light-- goto acttive idle
        if not self.eyes.IsDark():
            STATE.ChangeState('ActiveIdle')
        else: self.Sleep(sleep_secs.get(STATE.GetState(), 0))

    #User has asked Lil3x to watch the house.  Take pictures of any movement and send them RIGHT AWAY!
    # Will not leave state until wakeword heard.  (Eventually woudl be nice to be able to recognise user
    def Surveil(self):
        if STATE.StateDuration() > (cf.g('SURVEIL_WAIT')*60) and self.eyes.IsUserMoving():
            try:
                self.ai.say(self.ai.Intruder())
            except Exception as e: LogError(f"Surveil: exceoption on say()) {str(e)}")
            try:
                user_input = self.ai.listen()
            except Exception as e: LogError(f"Surveil: exception on listen()) {str(e)}")
            if user_input:
                try:
                    STATE.ChangeState('Active')
                    self.ai.say(self.ai.respond(user_input))
                except Exception as e: LogError(f"Surveil: exception on respond() {str(e)}")
            else:
                self.Sleep(cf.g('SURVEIL_LOOK')*60)  # don't send another notice for SURVEIL_WAIT minuntes
        else:
            self.Sleep(cf.g('SLEEP_DURATION'))
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
       os.system("sudo ./config/reboot.sh")

    def WaitThreads(self):
       threads = threading.enumerate()
       numThreads = len(threads)
       while numThreads > 0:
           threads = threading.enumerate()
           numThreads = len(threads)
           for t in threads:
               if re.search("^LilL3x", t.name): LogInfo(f"T={len(threads)} Waiting on {t.name}.")
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

print(f"LilL3x started at {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
l3x = lill3x()
l3x.Loop()
print(f"LilL3x exited at {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
