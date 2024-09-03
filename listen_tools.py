import speech_recognition as sr
import warnings
import sounddevice
from datetime import datetime, timedelta
from time import sleep
import pygame
import os
import sys
import inspect
from globals import MIC_STATE
from config import cf
from error_handling import RaiseError

class speech_listener:

    engine = 0
#    pygame_start = 0  # try to preload mp3s
#    pygame_end = 0

    def __init__(self):
        self.engine = cf.g('LISTEN_ENGINE')
        self.speech = sr.Recognizer()

        return

    def clear(self):
          self.listen(beQuiet=True, phrase_time_limit=1, adjust_for_ambient=2)
    
    def listen(self, beQuiet=False, time_out=cf.g('MIC_TO'), phrase_time_limit=cf.g('MIC_LIMIT'), adjust_for_ambient=cf.g('AMBIENT'), leds=False):
        imp = ""
        audio = False
        dt = datetime.now()
        if MIC_STATE.TakeMic(time_out):
            with sr.Microphone() as source:
                self.speech.adjust_for_ambient_noise(source, adjust_for_ambient)
            
                if not beQuiet:
                    self.PlayFile(cf.g('START_LISTEN_MP3'))

                if leds:
                    leds.listening()
 
                try:
                    audio = self.speech.listen(source, timeout=time_out, phrase_time_limit=phrase_time_limit)
                except sr.exceptions.WaitTimeoutError:
                    pass
                except Exception as e:
                    MIC_STATE.ReturnMic()
                    return RaiseError("speech_listener.listener() returned error:" + str(e))

                if leds:
                    leds.thinking()

                if not beQuiet:
                    self.PlayFile(cf.g('END_LISTEN_MP3'))

                if audio:
                    try:
#                        imp = self.speech.recognize_google(audio)
                        imp = eval(f"self.speech.recognize_{self.engine}(audio)")
                    except sr.exceptions.UnknownValueError:
                        pass
                    except Exception as e:
                        MIC_STATE.ReturnMic()
                        return RaiseError("speech_listener.recognize_google() returned error:" + str(e))

                #imp = self.engines['google')(audio)  ## NEEED FIX
                MIC_STATE.last = datetime.now()
                print(f"User: '{imp}'\n  Elapsed seconds:{(datetime.now()-dt).seconds}")
                MIC_STATE.ReturnMic()
                if leds:
                    leds.off()
                return imp

    def Close(self):
        return
 
    def Evesdrop(self):
        return self.listen(True)

    def CanIHearYou(self, dur=30):
        return self.listen(True, phrase_time_limit=dur) != ""

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
            print("Sphinx RequestError; {0}".format(e))

    def google(self, audio):
        try:
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            if cf.g('GOOGLE_API'):
                self.speech.recognize_google(audio, key=cf.g('GOOGLE_API'))
            else:
                self.speech.recognize_google(audio)
        except sr.RequestError as e:
            print("Google Speech Recognition service RequestError; {0}".format(e))

    def vosk(self, audio):
        try:
            return self.speech.recognize_vosk(audio)
        except sr.RequestError as e:
            print("Sphinx RequestError; {0}".format(e))
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

# recognize speech using whisper
try:
    print("Whisper thinks you said " + r.recognize_whisper(audio, language="english"))
except sr.UnknownValueError:
    print("Whisper could not understand audio")
except sr.RequestError as e:
    print(f"Could not request results from Whisper; {e}")

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
                print("Unable to get mic (timeout)")
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
 #       print(f"Listen_tools:CanUse: self.mic_free={self.mic_free}, self.request_mic={self.request_mic}")
        return (not self.request_mic and self.mic_free)
        return True

if __name__ == '__main__':
    pygame.mixer.init()
    sg = speech_listener()
    sg.clear()
#    while True:
#        print("Can I hear you?", end="")
#        print(sg.CanIHearYou())
    txt = ""
    print("Engine: ", end="")
    sg.engine = input()
    while txt != 'quit':
        dt  = datetime.now()
        print("Timeout: ", end="")
        to = input()
        print("Phrase Limit: ", end="")
        pl = input()
        txt = sg.listen(False, int(to), int(pl))
        print(txt)
        print(f'\nElapsed Seconds: {(datetime.now()-dt).seconds}')

