
# pre trained
#model: alexa
#model: hey_mycroft
#model: hey_jarvis

import argparse
import os
from pathlib import Path
import struct
import wave
import pygame
import numpy as np
import sounddevice as sd
from datetime import datetime
from globals import STATE,  MIC_STATE
from time import sleep
from error_handling import *
from pvrecorder import PvRecorder
from config import cf
import openwakeword
from openwakeword.model import Model

LogInfo("Importing openWakeWord Wake...")
class openWakeWord_wake:

    is_speaking = False
    should_quit = False
    ww_listener = None
    audio_device_index = -1  #RaspberryPI  TODO PULL FROM GLOBALS
    volume = 0
    wake_word = ""

    def __init__(self, face=False):
        self.keywords_path = [cf.g('WAKEWORD_PATH')]
        self.wake_mp3 = pygame.mixer.Sound(cf.g('WAKE_MP3'))
        self.SetWakeWord()

    def BuildPaths(self, path=cf.g('WAKEWORD_PATH')):
        paths = []

        if os.path.isdir(path):
            for root, dirs, files in os.walk(path, ):
                for file in files:
                    del dirs[:]
                    if os.path.isdir(file): continue
                    path = (os.path.join(root, file))
                    paths.append(path)
        else:
            paths.append(path)
        return paths

    def SetWakeWord(self, new_wake=cf.g('OPENWAKEWORD_WAKEWORD')):
        MIC_STATE.TakeMic()  #Pause the listening thread to replace the listener object
        keywords_path = self.BuildPaths(new_wake)
        self.wake_word = Path(os.path.basename(new_wake)).stem
        try:
            LogDebug(f"self.ww_listener = Model(wakeword_models={keywords_path})")
            self.ww_listener = Model(wakeword_models=keywords_path) #wakeword_models=["path/to/model.tflite"])
            LogInfo(f"Wake Word Set to: {cf.g('OPENWAKEWORD_WAKEWORD')}.")
        except Exception as e: LogError(f"Failed to initialize openWakeWord {e.args}")

        MIC_STATE.ReturnMic()

    def ww_thread(self):

        LogInfo("openWakeWord Listen Thread started")
        while not self.should_quit and self.ww_listener:
            if not STATE.IsInteractive():     #don't bother listening if in Active or Wake
                if (MIC_STATE.CanUse()):
                    MIC_STATE.TakeMic()
                    self.listen_loop()
                    MIC_STATE.ReturnMic()
                    sleep(1) # sleep for a sec to give listen_tools a chance to grab the mic
                else:
                    while not self.should_quit and (not MIC_STATE.MicFree() or MIC_STATE.MicRequested()): sleep(1)
            else:
                # no wakeword on Wake/Active states
                continue
        LogInfo("WW Listen Thread ended")

    def listen_loop(self):
        LogDebug("openWakeWord_wake listen_loop started")
        avgDelta = 1
        if not self.ww_listener:
            LogWarn("Not starting Wake word: no listener")
            return
        recorder = None
        try:
            recorder = PvRecorder(frame_length=512, device_index=self.audio_device_index)
        except Exception as e:
            return LogError(f"openWakeWord listen_loop: Exception when creating recorder: {str(e)})")
        if not recorder: return LogError(f"openWakeWord listen_loop: Unable to create recorder.")

        recorder.start()
        while not (self.should_quit or STATE.IsInteractive()) and not MIC_STATE.MicRequested():
            try:
                pcm = recorder.read()
                STATE.volume = np.mean(np.abs(pcm))
                result = self.ww_listener.predict(np.array(pcm))
                if result[self.wake_word] >= cf.g('OPENWAKEWORD_THRESHOLD'):
                    self.ww_listener.reset()
                    LogInfo(f"Wake word heard {self.wake_word}: {result[self.wake_word]}")
                    if not pygame.mixer.get_busy():
                        STATE.ChangeState('Wake')
                        self.wake_mp3.play()
                    else: LogInfo(f"Wake word ignored, audio playing")
            except Exception as e:
                LogError(f"openWakeWord_wake listen_loop encountered exception: {e.args})")

        #mic is requested
        recorder.stop()  # stop the recorder if requested to do so
        recorder.delete()
        sd.default.reset()
        LogDebug("openWakeWord_wake listen_loop ended")
        return
    
    def GetVolume(self):
        return STATE.volume

    def GetWakePhrase(self):
        return False

    def Close(self):
        LogInfo("Exiting openWakeWord_wake")
        self.should_quit = True

    def IsUserSpeaking(self, quiet=0):
        return STATE.volume>quiet

if __name__ == '__main__':
   import threading
   from time import sleep
   global STATE
   STATE.ChangeState('Idle')
   pygame.mixer.init()

   openwakeword.utils.download_models()
   ww = openWakeWord_wake()
   t = threading.Thread(target=ww.ww_thread)
   t.start()

   new = ""
   while new != 'quit':
       if STATE.CheckState('Wake'):
           STATE.ChangeState('Active')
           STATE.ChangeState('Idle')
       new = input("new WW path:" )
       if new=="quit": break
       elif new: 
           ww.SetWakeWord(new)
           print(ww.keywords_path)
   ww.Close()
   print("main: waiting for thread", end="")
   while t.is_alive():
      print(".", end="")
      sleep(1)
