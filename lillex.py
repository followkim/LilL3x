#!/usr/bin/env python3

import os
import sys
import inspect
from pathlib import Path
import logging
import threading
import time
from error_handling import RaiseError
from time import sleep
from datetime import datetime, timedelta
from multiprocessing import Process
import signal
import sys
from globals import STATE
from hardware import HW
import wake_word
from error_handling import RaiseError
from config import cf
from gpiozero import CPUTemperature
import RPi.GPIO as GPIO
BUTTON = 17

from speech_tools import speech_generator
from listen_tools import speech_listener
from camera_tools import Camera

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
print(currentdir)

# import AI sub modules
sys.path.insert(0, currentdir+'/beings/')
from AI_Dude import AI_Dude
from AI_Openai import *
from AI_Kindriod import AI_Kindriod
from AI_Gemini import AI_Gemini
#from AI_Bard import AI_Bard
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
    ww_thread = 0
    button_thread = 0
    def __init__(self):

        
        # get AI (depending on config)
        try:
            self.ai = eval("AI_"+cf.g('AI_ENGINE')+"()")
            self.ai.SetBody(HW.ears, HW.eyes, HW.mouth, HW.leds)

        except Exception as e:
            RaiseError("Unable to create AI: "+ str(e))
        if not self.ai:
            RaiseError("Unable to create AI: init failed")
 
        STATE.ChangeState('Hello')
        

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON, GPIO.IN)

        # finally start the wakeword thread
        self.ww_thread = threading.Thread(target=wake_word.Wake_word_thread, args=(HW.mouth,))
        self.ww_thread.start()
        self.button_thread = threading.Thread(target=self.ButtonThread)
        self.button_thread.start()
#        self.ww_thread.join()

    def Loop(self):
        while STATE.GetState() != 'Quit':
            temp = CPUTemperature().temperature
            if temp >= cf.g('CPU_MAX_TEMP'):
                if temp >= 80:
                    HW.say(f"I am {temp} degrees celcius, and that's too hot. Let me cool down and we'll try again.")
                    RaiseError(f"Heat error: {temp}.  Quitting.")
                    STATE.ChangeState('Quit') 
                else: sleep(2)
            eval("self."+STATE.GetState()+"()")
        self.Quit()

    def ChangeAI(self):
        STATE.ChangeState('Active')
        print(f"Changing AI to {STATE.data}.")
        new_ai = 0

        try:
            new_ai = eval("AI_" + STATE.data + "()")

        except Exception as e:
#            RaiseError("Unable to create AI: "+ str(e))  Don't raise an error-- too often just a missed word
            self.ai.say(f"I wasn't able to switch to {STATE.data}.  {str(e)}")
            return None
        if not new_ai.has_auth:
            RaiseError("Unable to create AI: auth failed")
            self.ai.say(f"I wasn't able to switch to {STATE.data}.  Authorization error.")
            return None
        
        # were able to create the AI!
        self.ai.Close()
        self.ai = new_ai
        self.ai.SetBody(HW.ears, HW.eyes, HW.mouth, HW.leds)

        STATE.ChangeState('Hello')
        return True

    # Hello: Give a greeting to the user:
    def Hello(self):
        HW.ears.clear()
        self.ai.say(self.ai.Hello())
        STATE.ChangeState('Active')
        return

    def Quit(self):
#       self.ww_thread.kill()  # will exit on its own
       HW.Close()
       self.ai.Close()
       cf.WriteConfig()
       exit()

    # Wake: AI has just been summoned by user at any time.  Also the entry point into the loop
    def Wake(self):
      #  print("Wake State")
      #  self.ai.say(self.ai.WakeMessage())
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
        if STATE.StateDuration() > timeout_secs.get(STATE.GetState(), 0):
            STATE.ChangeState('Idle')

        if HW.eyes.IsDark():
             STATE.ChangeState('SleepState')
        elif self.ai.LookForUser(cf.g('LOOK_SECS_TO_DEFAULT')):
            HW.leds.purple()
            thought = self.ai.Interact()  
            HW.leds.off()
            if thought:
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
        if HW.eyes.IsDark():
            STATE.ChangeState('SleepState')

        # Check for the user
        else:
            is_user_there = self.ai.LookForUser(cf.g('LOOK_SECS_TO_DEFAULT'))
            if is_user_there:
                STATE.ChangeState('ActiveIdle')  # siliently move into Active state, might want to Interact right away?
            else:
                self.Sleep(sleep_secs.get(STATE.GetState(), 0))

    # Sleep: User is not present.   User needs to use wakeword or respond to "welcome back" to activate ai
    #       AI can: machine learning, check lights/sound
    def SleepState(self):

        # IDEA: start a IsDark Camera thread that will change the state
 
        # user returned
        if not HW.eyes.IsDark() and self.ai.LookForUser(cf.g('LOOK_SECS_TO_DEFAULT')):
            self.ai.say(self.ai.Greet())
            user_input = self.ai.listen()
            if user_input:
                self.ai.say(self.ai.respond(user_input))
                STATE.ChangeState('Active')
            else:
                STATE.ChangeState('ActiveIdle')
        else:
            self.Sleep(sleep_secs.get(STATE.GetState(), 0))

    #User has asked Lil3x to watch the house.  Take pictures of any movement and send them RIGHT AWAY!
    # Will not leave state until wakeword heard.  (Eventually woudl be nice to be able to recognise user
    def Surveil(self):
        # DEBUG: change 1 to 60 when working
        if STATE.StateDuration() > (cf.g('SURVEIL_WAIT')*60) and HW.eyes.IsUserMoving(secs=cf.g('SURVEIL_LOOK')):
            self.ai.say(self.ai.Intruder())
            user_input = self.ai.listen()
            if user_input:
                self.ai.say(self.ai.respond(user_input))
                STATE.ChangeState('Active')      # this will turn off the system if the TV is on or something
            else:
                self.Sleep(cf.g('SURVEIL_WAIT')*60)  # don't send another notice for SURVEIL_WAIT minuntes
        else:
            self.Sleep(cf.g('SLEEP_DURATION'))
        return

     # A version of sleep that will break out if the state changes by WakeWord.   Avoids long period of uninterruptable sleep.
    def Sleep(self, secs):
        global STATE
        curr_state = STATE.GetState()
        target_time = datetime.now() + timedelta(seconds=secs)
        sleep_for = min(cf.g('SLEEP_DURATION'), secs)
        while (datetime.now() < target_time) and STATE.GetState() == curr_state and not STATE.IsInteractive():
            sleep(sleep_for)

    def ButtonThread(self):
        while STATE.GetState() not in ('Quit'):
            if not STATE.IsInteractive() and not (GPIO.input(BUTTON)):
                STATE.ChangeState('Wake')
                print("Button Wake")
                while (GPIO.input(BUTTON)):
                     continue
            else:
               sleep(1)
        print("ButtonThread exit.")

## THREADING INFO
os.chdir(sys.path[0])
l3x = lill3x()
l3x.Loop()
