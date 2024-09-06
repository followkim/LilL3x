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
from datetime import datetime
from globals import STATE,  MIC_STATE
from time import sleep
from error_handling import RaiseError
import pvporcupine
from pvrecorder import PvRecorder
from config import cf

class wake_word:

    wakeword_listener = None
    keyword_path = None
    recorder = None
    audio_device_index = 2  #RasperbyPI  TODO PULL FROM GLOBALS
    keyword_paths = []
    keywords = []
    audio = 0
    def __init__(self, audio):
        self.audio = audio
        for x in os.listdir(cf.g('WAKEWORD_PATH')):
            self.keyword_paths.append(cf.g('WAKEWORD_PATH')+x)
        
        
        try:
            self.wakeword_listener = pvporcupine.create(
                access_key=cf.g('PICOVOICE_KEY'),
                keyword_paths=self.keyword_paths #DOTO pass k eywords list: wakeword, amazon, google siri?
        #        keywords = ('elektra')
        #                library_path=args.library_path,
        #                model_path=args.model_path,
        #                sensitivities=args.sensitivities
                )
        except pvporcupine.PorcupineInvalidArgumentError as e:
            print("One or more arguments provided to Porcupine is invalid: ", args)
            print(e)
            raise e
        except pvporcupine.PorcupineActivationError as e:
            print("AccessKey activation error")
            raise e
        except pvporcupine.PorcupineActivationLimitError as e:
            print("AccessKey '%s' has reached it's temporary device limit" % args.cf.g('PICOVOICE_KEY'))
            raise e
        except pvporcupine.PorcupineActivationRefusedError as e:
            print("AccessKey '%s' refused" % args.cf.g('PICOVOICE_KEY'))
            raise e
        except pvporcupine.PorcupineActivationThrottledError as e:
            print("AccessKey '%s' has been throttled" % args.cf.g('PICOVOICE_KEY'))
            
            raise e
        except pvporcupine.PorcupineError as e:
            print("Failed to initialize Porcupine")
            raise e

        wakewords = list()
        for x in cf.g('WAKEWORD_PATH'):
            wakeword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
            if len(wakeword_phrase_part) > 6:
                self.keywords.append(' '.join(wakeword_phrase_part[0:-6]))
            else:
                self.keywords.append(wakeword_phrase_part[0])

        print('Porcupine version: %s' % self.wakeword_listener.version)

    def listen(self, beQuiet=False):
        

        global should_quit
        global STATE
        global MIC_STATE

        # create a recorder
        try:
            self.recorder = PvRecorder(frame_length=self.wakeword_listener.frame_length, device_index=self.audio_device_index)
        except Exception as e:
            return RaiseError("Unable to create recorder: " + str(e))
        while not STATE.CheckState('Quit'):
            if not STATE.IsInteractive():     #don't bother listening if in Active or Wake
                if (MIC_STATE.CanUse()):
                    MIC_STATE.TakeMic()
                    self.recorder.start()
#                    print ("WakeWord: taking the mic")

                    while (not MIC_STATE.MicRequested() and not (STATE.CheckState('Quit) or STATE.IsInteractive()):
                        try:
                            pcm = self.recorder.read()
                            result = self.wakeword_listener.process(pcm)
                            # TODO: put this in a "wake" function to share with the button
                            if result >= 0:
                                STATE.ChangeState('Wake')
                                if not self.audio.IsBusy():
                                    self.audio.PlaySound(cf.g('WAKE_MP3'))
                                print(f"Wake word heard: {result}") # : %s" % self.keywords[result])
                        except Exception as e:
                            print("WakeWord loop encountered exception: " + str(e))
#                            self.Close()
                    # end while loop
                
                    #mic is requested
                    self.recorder.stop()  # top the recorder if requested to do so
                    MIC_STATE.ReturnMic()
                    sleep(1) # sleep for a sec to give listen_tools a chance to grab the mic
                else:
                    while (not MIC_STATE.MicFree() or MIC_STATE.MicRequested()):
                        sleep(1)
                        
            else:
                # no wakeword on Wake/Active states
                continue
        self.recorder.delete()
        self.Close()


    def Close(self):
        print("Exiting WakeWord")
        self.wakeword_listener.delete()
        exit()
        
def Wake_word_thread(audio):
    ww = wake_word(audio)
    ww.listen()


if __name__ == '__main__':
   from speech_tools import speech_generator

   global STATE
   STATE.ChangeState('Idle')
   mouth = speech_generator()


   Wake_word_thread(mouth)
