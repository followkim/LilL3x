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
import sounddevice as sd
from datetime import datetime
from globals import STATE,  MIC_STATE
from time import sleep
from error_handling import *
import pvporcupine
from pvrecorder import PvRecorder
from config import cf

class wake_word:
    is_speaking = False
    
    wakeword_listener = None
    audio_device_index = -1  #RasperbyPI  TODO PULL FROM GLOBALS
#    keyword_paths = []
    keywords = []
    audio = 0
    def __init__(self, audio):
        self.audio = audio
        keyword_path = [cf.g('AINAMEP')]
        try:
            self.wakeword_listener = pvporcupine.create(
                access_key=cf.g('PICOVOICE_KEY'),
                keyword_paths=keyword_path #DOTO pass k eywords list: wakeword, amazon, google siri?
        #        keywords = ('bumblebee')
        #                library_path=args.library_path,
        #                model_path=args.model_path,
        #                sensitivities=args.sensitivities
                )
        except pvporcupine.PorcupineInvalidArgumentError as e:
            LogError("One or more arguments provided to Porcupine is invalid: ", args)
            LogError(e)
            raise e
        except pvporcupine.PorcupineActivationError as e:
            LogError("AccessKey activation error")
            raise e
        except pvporcupine.PorcupineActivationLimitError as e:
            LogError("AccessKey '%s' has reached it's temporary device limit" % args.cf.g('PICOVOICE_KEY'))
            raise e
        except pvporcupine.PorcupineActivationRefusedError as e:
            LogError("AccessKey '%s' refused" % args.cf.g('PICOVOICE_KEY'))
            raise e
        except pvporcupine.PorcupineActivationThrottledError as e:
            LogError("AccessKey '%s' has been throttled" % args.cf.g('PICOVOICE_KEY'))
            
            raise e
        except pvporcupine.PorcupineError as e:
            LogError("Failed to initialize Porcupine")
            raise e

        wakewords = list()
        for x in cf.g('WAKEWORD_PATH'):
            wakeword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
            if len(wakeword_phrase_part) > 6:
                self.keywords.append(' '.join(wakeword_phrase_part[0:-6]))
            else:
                self.keywords.append(wakeword_phrase_part[0])

        LogInfo('Porcupine version: %s' % self.wakeword_listener.version)

    def listen(self, beQuiet=False):
        
        recorder = 0
        # create a recorder
        LogInfo("WW Listen Thread started")
        while not STATE.CheckState('Quit'):
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
        self.Close()
        LogInfo("WW Listen Thread ended")
    def listen_loop(self):
        LogDebug("ww listen_loop started")
        try:
            recorder = PvRecorder(frame_length=self.wakeword_listener.frame_length, device_index=self.audio_device_index)
        except Exception as e:
            return RaiseError("Unable to create recorder: " + str(e))
        recorder.start()
        while (not MIC_STATE.MicRequested() and not (STATE.CheckState('Quit') or STATE.IsInteractive())):
            try:
                pcm = recorder.read()
                result = self.wakeword_listener.process(pcm)
                # TODO: put this in a "wake" function to share with the button
                if result >= 0:
                    STATE.ChangeState('Wake')
                    if not self.audio.IsBusy():
                        self.audio.PlaySound(cf.g('WAKE_MP3'))
                        LogInfo(f"Wake word heard: {result}") # : %s" % self.keywords[result])
            except Exception as e:
                LogError("WakeWord loop encountered exception: " + str(e))
                
        #mic is requested
        recorder.stop()  # stop the recorder if requested to do so
        recorder.delete()
        sd.default.reset()
        LogDebug("wakeword listen_loop ended")
        return

    def GetWakePhrase(self):
        return False

    def Close(self):
        LogInfo("Exiting WakeWord")
        self.wakeword_listener.delete()
        exit()
        

if __name__ == '__main__':
   from speech_tools import speech_generator
   import threading
   from time import sleep
   global STATE
   STATE.ChangeState('Idle')
   mouth = speech_generator()

   ww = wake_word(mouth)
   t = threading.Thread(target=ww.listen)
   t.start()
   while True:
      if STATE.CheckState('Wake'):
          STATE.ChangeState('Active')
          STATE.ChangeState('Idle')
      sleep(5)
      print("STATE= " + STATE.GetState())
