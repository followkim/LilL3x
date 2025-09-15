#!/usr/bin/env python3
#import welcome
import os
import sys
import re
import subprocess
import pygame

os.chdir(f"/home/el3ktra/LilL3x/")
sys.path.append(f"/home/el3ktra/LilL3x/")

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
from globals import STATE, SleepOn, HasInternet
from config import cf

from listen_tools import SpeechRecognition_listener
from speech_tools import speech_generator
from face import Face

currentdir = os.getcwd()

LogInfo("Importing AI...")
sys.path.insert(0, currentdir+'/beings/')
from AI_Dude import AI_Dude
from AI_Openai import *
from AI_Ollama import *
from AI_Kindroid import AI_Kindroid
from AI_Gemini import AI_Gemini
from AI_Claude import AI_Claude
from AI_Nomi import AI_Nomi

sys.path.insert(0, currentdir+'/raspberryPi/')
from button import Button
from purr import Purr

sys.path.insert(0, currentdir)


class lill3x:

    ai = False
    ears = False
    mouth = False
    face = False

    button = False
    purr = False

    wifi = True

    def __init__(self):
        isRestart = False
        if '--restart' in sys.argv:       # if restart, don't say hello or play the welcome bell
            isRestart = True
            LogInfo("Resuming after restart")

        pygame.mixer.init()

#        InitLogFile()  This is done above to capture log messages while loading externals
        LogInfo(f"Starting {GetHostname()}")

        try:
            self.mouth = speech_generator()
        except Exception as e:
            RaiseError(f"Init():Could not init speech generator. {e.args}")
            STATE.ChangeState('Quit')
            return # fatal

        try:
            self.face = Face() # note this spawns two threads: animate and led threads.  The face will appear here.
        except Exception as e:
            RaiseError(f"Init():Could not init Eyes. {e.args}")

        try:
            self.ears = eval(f"{cf.g('LISTEN_ENGINE')}_listener(self.face)")
        except Exception as e:
            RaiseError(f"Init():Could not init listener. {e.args}")
            STATE.ChangeState('Quit')
            return # fatal

        if not isRestart: self.mouth.PlaySound(cf.g('STARTUP_MP3'), asyn=True)  # play the startup tone


        try:
            self.button = Button()
            button_thread = threading.Thread(target=self.button.ButtonThread, args=(self.mouth,), daemon=True)
            button_thread.name = f"{GetHostname()} ButtonThread"
            button_thread.start()
        except Exception as e:
            RaiseError(f"Init():Could not init Button. {e.args}")

        try:
            self.purr = Purr()
            purr_thread = threading.Thread(target=self.purr.PurrThread, args=(self.mouth,self.face,), daemon=True)
            purr_thread.name = f"{GetHostname()} PurrThread"
            purr_thread.start()
        except Exception as e:
            RaiseError(f"Init():Could not init Purring. {e.args}")

        while not HasInternet():
            LogInfo("Waiting for Internet...")
            sleep(5)


        # get AI
        try:
            self.ai = eval(f"AI_{cf.g('AI_ENGINE')}()")
            self.ai.SetBody(self.ears, self.mouth, self.face)
        except Exception as e:
            RaiseError(f"Unable to create AI: {e.args}")
            STATE.ChangeState('Quit')
            return # fatal

        if not self.ai:
            RaiseError("Unable to create AI: init failed")
            STATE.ChangeState('Quit')
            return



        
        # THREADS : WW and config
        config_thread = threading.Thread(target=cf.config_thread, daemon=True)
        config_thread.name = f"{GetHostname()} ConfigThread"
        config_thread.start()

        if isRestart:
            try: self.ai.last_ai_interaction = datetime.strptime(cf.g('LAST_INTERACTION'), cf.g('CONFIG_DT_FORMAT'))
            except: self.ai.last_ai_interaction = datetime.now()
            LogInfo(f"Last Interaction:  {self.ai.last_ai_interaction.strftime('%B %d, %Y %I:%M %p')}.")
            STATE.ChangeState('SleepState')
        else:
            STATE.ChangeState('Hello')

    def Loop(self):
        LogInfo("Starting Main Loop")
        last_err = False  # we can ignore a single error... but if there are two in a row then quit.
        while not STATE.ShouldQuit():
            STATE.HWState(cf.g('DEBUG'))  # will only update every 10 secs
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
        '''Called via a ChangeState'''
        LogInfo(f"Changing AI to {STATE.data}.")
        if self.SwitchAI(STATE.data):
            STATE.ChangeState('Hello')
            cf.WriteConfig()
            return True
        else: STATE.RevertState()
  

    def SwitchAI(self, newAI):
        '''called directly from EvalCode'''
        try:
            new_ai = eval(f"AI_{newAI}()")

        except Exception as e:
            LogError(f"Unable to create AI: {e.args}")
            self.ai.say(f"I wasn't able to switch to {newAI}.  {e.args}")
            return False

        if not new_ai.has_auth:
            LogError("Unable to create AI {newAI}: auth failed")
            self.ai.say(f"I wasn't able to switch to {newAI}.  Authorization error.")
            return False

        # were able to create the AI!
        self.ai.Close() # blocking, no threads
        self.ai = new_ai
        self.ai.SetBody(self.ears, self.mouth, self.face)
        cf.s('AI_ENGINE', newAI)
        return True

    def ChangeListener(self):
        LogInfo(f"Changing Listener to {STATE.data}.")
        if self.SwitchListener(STATE.data):
            cf.WriteConfig()
        STATE.RevertState()

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
        return True

    def EvalCode(self):
        '''EvalCode: Runs the commands stored in the STATE.data field.  
                 Used to make changes such as chaning AI, wake work, or speech generator.
                 Called from config thread.'''
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
        '''Hello: called at the very start of a reboot.  Skipped on restart.  Greets the user'''
        self.ai.say(self.ai.Hello())  #TODO - give a greeting at first meet
        STATE.ChangeState('Active')
        return

    # Wake: AI has just been summoned by user at any time.  Also the entry point into the loop
    def Wake(self):
        '''Wake: called when the STATE is changed to Wake by wake_word or button threads'''
        self.face.thinking()
        STATE.ChangeState('Active')

        # check for connectivity
        if self.wifi or self.WifiOn():
            if cf.g('SHOULD_GREET'): self.ai.say(self.ai.respond(cf.g('WAKEPHRASE')))
        else:
            self.mouth.PlaySound(cf.g('ERROR_FILE'))
            STATE.ChangeState('SleepState')
            self.face.off()

    def Active(self):
        ''' Active: User is present and activly talking to ai without need for wakeword
        ''          AI can: listen and respond to user'''
        user_input = self.ai.listen()
        if user_input:
            self.ai.say(self.ai.respond(user_input))
        else:
            STATE.ChangeState('SleepState')

    def SleepState(self):
        ''' Sleep: Lights are off.  AI Hardware is turned off.
        ''         AI can: machine learning, check lights/sound '''
        if STATE.StateDuration() > 60 * cf.g('WIFI_OFF'):
            self.WifiOff()
            SleepOn(step=1) #sleep until state change
        else:
            SleepOn(secs=(60*cf.g('WIFI_OFF'))+1, step=1)  # deep sleep

    def Quit(self):

       if self.wifi or self.WifiOn(): LogDebug("Wifi on")
       else: LogError("Wifi could not be turned on")

       if self.ai: self.ai.Close()
       if self.mouth: self.mouth.Close()
       if self.ears: self.ears.Close()
       if self.purr: self.purr.Close()
       if self.face: self.face.Close()
       cf.Close()
       self.WaitThreads()
       CloseLog()

    def Restart(self):
       self.Quit()
       try:
           python = sys.executable
           args = [sys.argv[0], "--restart"]
           cmd = [python] + args
           LogDebug(f"Restart cmd: {cmd}")
           process = subprocess.Popen(cmd, start_new_session=True)
#       with open('process_output.txt', 'w') as outfile:
#           process = subprocess.Popen(cmd, stdout=outfile, stderr=outfile)
#           process.wait()
 #      LogDebug(f"Popen returned {process.returncode}")
           sleep(10)
       except Exception as e:
           LogError(f"Unable to restart.  {e.args}")
    def Reboot(self):
       self.Quit()
       os.system("sudo reboot")

    def WaitThreads(self):
       start = datetime.now()
       threads = threading.enumerate()
       numThreads = len(threads)
       while numThreads > 0 and (datetime.now()-start).total_seconds() < 30: # force quit after 30 seconds
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

    def WifiOff(self):
        """Turns off the Wi-Fi interface (wlan0) on a Raspberry Pi."""
        try:
            LogInfo("Turning off Wi-Fi...")
            # Command to bring down the wlan0 interface
            cmd = 'sudo ifconfig wlan0 down'
            os.system(cmd)
            self.wifi = False
        except Exception as e:
            LogError(f"Error turning off Wi-Fi: {e}")

    def WifiOn(self):
        """Turns on the Wi-Fi interface (wlan0) on a Raspberry Pi."""
        try:
            # Command to bring up the wlan0 interface
            cmd = 'sudo ifconfig wlan0 up'
            os.system(cmd)
            LogInfo("Wi-Fi turned on.")
        except Exception as e:
            LogError(f"Error turning on Wi-Fi: {e.args}")

        wait = datetime.now() + timedelta(seconds=60)  # wait for the internet for 60 secondss
        while not HasInternet() and wait > datetime.now():
            sleep(2)
        self.wifi = HasInternet()
        if not self.wifi: LogError("Not able to reach internet after turning on wifi.")
        return self.wifi

## THREADING INFO
#os.chdir('/home/el3ktra/LilL3x/')
# Get the current working directory

print(f"{GetHostname()} started at {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
l3x = lill3x()
l3x.Loop()
print(f"{GetHostname()} exited at {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
