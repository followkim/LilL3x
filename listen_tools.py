import speech_recognition as sr
import warnings
import sounddevice
from datetime import datetime, timedelta
from time import sleep
import pygame
import os
import sys
import inspect
from globals import MIC_STATE, STATE
from config import cf
from error_handling import *
import threading
 
def dummy():
    return
LogInfo("Listen Engine Loading...")

class speech_listener:

    engine = 0
#    pygame_start = 0  # try to preload mp3s
#    pygame_end = 0
    start_mp3 = 0
    end_mp3 = 0
    audio = 0
    def __init__(self):
        self.speech = sr.Recognizer()
#        self.speech.dynamic_energy_ratio = 2
        self.update()
        self.start_mp3 = pygame.mixer.Sound(cf.g('START_LISTEN_MP3'))
        self.end_mp3 = pygame.mixer.Sound(cf.g('END_LISTEN_MP3'))
        return

    def clear(self):
#          self.listen(beQuiet=True, adjust_for_ambient=2)
          return   

    def update(self, asyn=False, needMic=True):
        if asyn:
            update_thread = threading.Thread(target=self.update_thread)
            update_thread.start()

        else: self.update_thread(True)

    def update_thread(self, adjust_for_ambient=cf.g('AMBIENT'), needMic=False):
        self.speech.pause_threshold = cf.g('MIC_LIMIT')
        self.speech.dynamic_energy_threshold = cf.g('ENERGY_DYNAMIC')==1

        if not needMic or MIC_STATE.TakeMic(cf.g('MIC_TO')):
            with sr.Microphone() as source:
                self.speech.adjust_for_ambient_noise(source, adjust_for_ambient)
            LogInfo(f"energy thresh={round(self.speech.energy_threshold)} x {1 + (cf.g('ENERGY_THRESH')/100.0)}")
            self.speech.energy_threshold = self.speech.energy_threshold * (1 + (cf.g("ENERGY_THRESH")/100.0))
            if needMic: MIC_STATE.ReturnMic()
        else: LogInfo(f"Ambeint: Unable to get Mic after {cf.g('MIC_TO')}s.")

    def listen_thread(self, source, timeout):
        try:
            self.audio = self.speech.listen(source, timeout)
        except sr.exceptions.UnknownValueError:
            pass
        except Exception as e:
            LogError(f"listen_thread error {str(e)}")


        
    def listen(self, beQuiet=False, face=False, time_out=cf.g('MIC_TO'), adjust_for_ambient=cf.g('AMBIENT')):
        imp = ""
        audio = False
        dt = datetime.now()
        self.speech.pause_threshold = cf.g('MIC_LIMIT')
        start_et = self.speech.energy_threshold
        if MIC_STATE.TakeMic(cf.g('MIC_TO')):
            with sr.Microphone() as source:
            #    self.speech.adjust_for_ambient_noise(source, adjust_for_ambient)
            #    self.speech.energy_threshold = self.speech.energy_threshold * 1.25

                if not beQuiet:
                    self.start_mp3.play()
                    if face: face.listening()
                try:
#                    audio = self.speech.listen(source, timeout=5.0) #,dynamic_energy_threshold=False)
                    self.audio = 0
                    listen_thread = threading.Thread(target=self.listen_thread, args=(source, time_out))
                    listen_thread.start()
                    run_avg = []
                    x=0
                    last_listen = datetime.now()
                    LogDebug(f"Energy:\tCurr\tThrsh\tC-T\tAvg\tSecs")
                    while listen_thread.is_alive():
                        x += 1
                        speaking_energy = round(self.speech.current_energy-self.speech.energy_threshold)
                        run_avg.append(speaking_energy) # should be positive if user is speaking
                        if (x % 120) == 0: # print debug string every 1 secs
                            LogDebug(f"Energy:\t{round(self.speech.current_energy)}\t{round(self.speech.energy_threshold)}\t{speaking_energy}\t{round(sum(run_avg)/len(run_avg))}\t{(datetime.now()-dt).seconds}s")
                        if len(run_avg) == 120:
                            run_avg.pop(0) # only keep 1s frames at a time
                            if (datetime.now()-last_listen).seconds>cf.g('MIC_TO'): ## after this many secs, check if user is really talkiung
                                if (sum(run_avg)/len(run_avg))<0:
                                    # they aren't talking, so start to jack up the threshold (limit to x4)
                                    self.speech.energy_threshold=min(self.speech.energy_threshold*1.25, start_et*4)
                                    run_avg.clear()
                                else: last_listen = datetime.now()
                        sleep(1/120)
                except Exception as e:
                    #force the listen thread to stop
                    while listen_thread.is_alive(): self.speech.energy_threshold=min(self.speech.energy_threshold*1.25, start_et*4)
                    MIC_STATE.ReturnMic()
                    LogError("speech_listener.listener() returned error:" + str(e))
                if not beQuiet:
                    self.end_mp3.play()
                    if face: face.thinking()
                if self.audio:
                    try:
                        self.update(asyn=True)
#                        imp = self.speech.recognize_google(audio)
                        imp = eval(f"self.speech.recognize_{cf.g('LISTEN_ENGINE')}(self.audio)")
                    except sr.exceptions.UnknownValueError:
                        pass
                    except Exception as e:
                        MIC_STATE.ReturnMic()
                        RaiseError(f"speech_listener.recognize_{cf.g('LISTEN_ENGINE')}() returned error: {str(e)}")
                    self.audio=False
                #imp = self.engines['google')(audio)  ## NEEED FIX
                MIC_STATE.last = datetime.now()
                LogConvo(f"{cf.g('USERNAME')}: '{imp}'  ({(datetime.now()-dt).seconds}s)")
                MIC_STATE.ReturnMic()
                #self.speech.energy_threshold = start_et
                self.update(asyn=True)
                if face: face.off()
        return imp

    def Close(self):
        return
 
    def Evesdrop(self):
        return self.listen(True)

    def CanIHearYou(self, dur=30):
        return self.listen(True, time_out=dur) != ""

    def PlayFile(self, file):
        try:
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                continue
        except Exception as e:
            RaiseError(f"Listener: unable to play file {file} ({str(e)})")

        return

    ####### Engines in here

    #Sphinx
    def sphinx(self, audio):
        try:
            return self.speech.recognize_sphinx(audio)
        except sr.RequestError as e:
            LogError("Sphinx RequestError; {0}".format(e))

    def google(self, audio):
        try:
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            if False: # cf.g('GOOGLE_API'):
                self.speech.recognize_google(audio, key=cf.g('GOOGLE_API'))
            else:
                self.speech.recognize_google(audio)
        except sr.RequestError as e:
            LogError("Google Speech Recognition service RequestError; {0}".format(e))

'''

    def googleCloud(self, audio):
        try:
            if cf.g('GOOGLE_API'):
                return self.speech.recognize_google_cloud(audio, credentials_json=cf.g('GOOGLE_CLOUD_SPEECH_CREDENTIALS'))
            else:
                self.speech.recognize_google(audio)
        except sr.RequestError as e:
            print("Google Speech Recognition service RequestError; {0}".format(e))


GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""INSERT THE CONTENTS OF THE GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE HERE""" #TODO Get from config
        try:
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            print("Google Speech Recognition thinks you said " + r.recognize_google(audio))
        except sr.RequestError as e:
            print("Google Speech Recognition service RequestError; {0}".format(e))

# recognize speech using Google Cloud Speech
GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""INSERT THE CONTENTS OF THE GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE HERE"""
try:
    print("Google Cloud Speech thinks you said " + r.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS))
except sr.UnknownValueError:
    print("Google Cloud Speech could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Google Cloud Speech service; {0}".format(e))

# recognize speech using Wit.ai
WIT_AI_KEY = "INSERT WIT.AI API KEY HERE"  # Wit.ai keys are 32-character uppercase alphanumeric strings
try:
    print("Wit.ai thinks you said " + r.recognize_wit(audio, key=WIT_AI_KEY))
except sr.UnknownValueError:
    print("Wit.ai could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Wit.ai service; {0}".format(e))

# recognize speech using Microsoft Bing Voice Recognition
BING_KEY = "INSERT BING API KEY HERE"  # Microsoft Bing Voice Recognition API keys 32-character lowercase hexadecimal strings
try:
    print("Microsoft Bing Voice Recognition thinks you said " + r.recognize_bing(audio, key=BING_KEY))
except sr.UnknownValueError:
    print("Microsoft Bing Voice Recognition could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))

# recognize speech using Microsoft Azure Speech
AZURE_SPEECH_KEY = "INSERT AZURE SPEECH API KEY HERE"  # Microsoft Speech API keys 32-character lowercase hexadecimal strings
try:
    print("Microsoft Azure Speech thinks you said " + r.recognize_azure(audio, key=AZURE_SPEECH_KEY))
except sr.UnknownValueError:
    print("Microsoft Azure Speech could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Microsoft Azure Speech service; {0}".format(e))

# recognize speech using Houndify
HOUNDIFY_CLIENT_ID = "INSERT HOUNDIFY CLIENT ID HERE"  # Houndify client IDs are Base64-encoded strings
HOUNDIFY_CLIENT_KEY = "INSERT HOUNDIFY CLIENT KEY HERE"  # Houndify client keys are Base64-encoded strings
try:
    print("Houndify thinks you said " + r.recognize_houndify(audio, client_id=HOUNDIFY_CLIENT_ID, client_key=HOUNDIFY_CLIENT_KEY))
except sr.UnknownValueError:
    print("Houndify could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Houndify service; {0}".format(e))

# recognize speech using IBM Speech to Text
IBM_USERNAME = "INSERT IBM SPEECH TO TEXT USERNAME HERE"  # IBM Speech to Text usernames are strings of the form XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
IBM_PASSWORD = "INSERT IBM SPEECH TO TEXT PASSWORD HERE"  # IBM Speech to Text passwords are mixed-case alphanumeric strings
try:
    print("IBM Speech to Text thinks you said " + r.recognize_ibm(audio, username=IBM_USERNAME, password=IBM_PASSWORD))
except sr.UnknownValueError:
    print("IBM Speech to Text could not understand audio")
except sr.RequestError as e:
    print("Could not request results from IBM Speech to Text service; {0}".format(e))


# recognize speech using Whisper API
OPENAI_API_KEY = "INSERT OPENAI API KEY HERE"
try:
    print(f"Whisper API thinks you said {r.recognize_whisper_api(audio, api_key=OPENAI_API_KEY)}")
except sr.RequestError as e:
    print(f"Could not request results from Whisper API; {e}")
    
'''


class MicStatus:
    def __init__(self):
        self.mic_free = True
        self.request_mic = False

    def TakeMic(self, timeout=3):
        self.request_mic = True
        ud = datetime.now() + timedelta(seconds=timeout)
        while not self.mic_free:
            self.request_mic = True    ## ask WW for the mic 
            if datetime.now() > ud:
                LogError("Unable to get mic (timeout)")
                return False
            continue
        self.mic_free = False
        self.request_mic = False
        return True

    def ReturnMic(self):
        self.request_mic = False
        self.mic_free = True
        return True

    def MicRequested(self):
        return self.request_mic

    def MicFree(self):
        return self.mic_free
    
    def CanUse(self):
        return (not self.request_mic and self.mic_free)
        return True
if __name__ == '__main__':
    pygame.mixer.init()
    sg = speech_listener()
    sg.update()
#    sg.engine="whisper"
#    while True:
#        print("Can I hear you?", end="")
#        print(sg.CanIHearYou())
    txt = ""
    while txt != 'quit':
        dt  = datetime.now()
#        print("Timeout: ", end="")
#        to = input()
#        print("Phrase Limit: ", end="")
#        pl = input()
        print("Speak")
        txt = sg.listen()
        print(txt)
        print(f'\nElapsed Seconds: {(datetime.now()-dt).seconds}')
        sleep(1)
