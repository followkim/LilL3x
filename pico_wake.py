#
# Copyright 2018-2023 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

import argparse
import os
import struct
import wave
import pygame
import sounddevice as sd
from datetime import datetime
from globals import STATE,  MIC_STATE
from time import sleep
from error_handling import *
import pvporcupine
from pvrecorder import PvRecorder
from config import cf

LogInfo("Importing Porcupine Wake...")
class pico_wake:
    is_speaking = False
    should_quit = False
    ww_listener = None
    audio_device_index = -1  #RasperbyPI  TODO PULL FROM GLOBALS
#    keyword_paths = []
    keywords_path = 0
    def __init__(self, face=False):
        self.keywords_path = [cf.g('WAKE_WORD')]
        self.wake_mp3 = pygame.mixer.Sound(cf.g('WAKE_MP3'))
        self.SetWakeWord()
        LogInfo('Porcupine version: %s' % self.ww_listener.version)

    def BuildPaths(self, path=cf.g('WAKE_WORD')):
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

    def SetWakeWord(self, new_wake=cf.g('WAKE_WORD')):
        MIC_STATE.TakeMic()  #Pause the listening thread to replace the listener object
        self.keywords_path = self.BuildPaths(new_wake)
        try:
           if self.ww_listener: self.ww_listener.delete()
           self.ww_listener = pvporcupine.create(access_key=cf.g('PICOVOICE_KEY'), keyword_paths=self.keywords_path)
        except pvporcupine.PorcupineInvalidArgumentError as e: LogError("One or more arguments provided to Porcupine is invalid: ", args)
        except pvporcupine.PorcupineActivationError as e: LogError("AccessKey activation error")
        except pvporcupine.PorcupineActivationLimitError as e: LogError("AccessKey '%s' has reached it's temporary device limit" % args.cf.g('PICOVOICE_KEY'))
        except pvporcupine.PorcupineActivationRefusedError as e: LogError("AccessKey '%s' refused" % args.cf.g('PICOVOICE_KEY'))
        except pvporcupine.PorcupineActivationThrottledError as e: LogError("AccessKey '%s' has been throttled" % args.cf.g('PICOVOICE_KEY'))
        except pvporcupine.PorcupineError as e: LogError("Failed to initialize Porcupine")
        except Exception as e: LogError(f"Failed to initialize Porcupine {str(e)}")

        MIC_STATE.ReturnMic()
        LogInfo(f"Wake Word Set to: {str(self.keywords_path)}.")

    def ww_thread(self):
        recorder = 0
        # create a recorder
        LogInfo("WW Listen Thread started")
        while not self.should_quit :
            if not STATE.IsInteractive():     #don't bother listening if in Active or Wake
                if (MIC_STATE.CanUse()):
                    MIC_STATE.TakeMic()
                    self.listen_loop()
                    MIC_STATE.ReturnMic()
                    sleep(1) # sleep for a sec to give listen_tools a chance to grab the mic
                else:
                    while (not MIC_STATE.MicFree() or MIC_STATE.MicRequested()):
                        sleep(1)
                        
            else:
                # no wakeword on Wake/Active states
                continue
        self.ww_listener.delete()
        LogInfo("WW Listen Thread ended")

    def listen_loop(self):
        LogDebug("ww listen_loop started")
        try:
            recorder = PvRecorder(frame_length=self.ww_listener.frame_length, device_index=self.audio_device_index)
        except Exception as e:
            return RaiseError("Unable to create recorder: " + str(e))
        recorder.start()
        while not MIC_STATE.MicRequested() and not (self.should_quit or STATE.IsInteractive()):
            try:
                pcm = recorder.read()
                result = self.ww_listener.process(pcm)
                # TODO: put this in a "wake" function to share with the button
                if result >= 0:
                    LogInfo(f"Wake word heard {self.keywords_path[result]}")
                    if not pygame.mixer.get_busy():
                        STATE.ChangeState('Wake')
                        self.wake_mp3.play()
                    else: LogInfo(f"Wake word ignored, audio playing")
            except Exception as e:
                LogError("pico_wake loop encountered exception: " + str(e))
                
        #mic is requested
        recorder.stop()  # stop the recorder if requested to do so
        recorder.delete()
        sd.default.reset()
        LogDebug("pico_wake listen_loop ended")
        return

    def GetWakePhrase(self):
        return False

    def Close(self):
        LogInfo("Exiting pico_wake")
        self.should_quit = True
        

if __name__ == '__main__':
   import threading
   from time import sleep
   global STATE
   STATE.ChangeState('Idle')
   pygame.mixer.init()
   ww = pico_wake()
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
