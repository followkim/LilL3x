import os
import speech_recognition as sr
import warnings
import sounddevice
from datetime import datetime, timedelta
from time import sleep
import pygame
import os
import sys
import inspect
from globals import STATE
from config import cf
from error_handling import *
import threading
from openai import OpenAI
import requests
import json

def dummy():
    return
LogInfo("Listen Engine Loading...")

class SpeechRecognition_listener:

    engine = 0
    start_mp3 = 0
    end_mp3 = 0
    audio = 0
    face = None
    quiet = 0

    def __init__(self, face=None):
        self.speech = sr.Recognizer()

#        self.speech.dynamic_energy_ratio = 2
#        self.update()

        self.start_mp3 = pygame.mixer.Sound(cf.g('START_LISTEN_MP3'))
        self.end_mp3 = pygame.mixer.Sound(cf.g('END_LISTEN_MP3'))
        self.face = face

        self.quiet = self.update()
        return

    def SetQuiet(self):
        self.quiet = self.update()
        return

    def GetQuiet(self):
        return self.quiet * (1 + (cf.g('QUIET_BOOST') / -100))

    def update(self, asyn=False, needMic=True):
        if asyn:
            update_thread = threading.Thread(target=self.update_thread)
            update_thread.name = f"{GetHostname()} SR.update_thread {update_thread.native_id}"
            update_thread.start()
            return update_thread
        else: return self.update_thread(needMic=needMic)

    def update_thread(self, adjust_for_ambient=cf.g('AMBIENT'), needMic=False):
        self.speech.pause_threshold = cf.g('MIC_LIMIT')
        self.speech.dynamic_energy_threshold = cf.g('ENERGY_DYNAMIC')==1

        if self.speech.dynamic_energy_threshold:  # vut 
            self.speech.dynamic_energy_adjustment_ratio = 1 + (cf.g('DYNAMIC_RATIO')/100.0)
            LogInfo(f"SR Update: Using dynamic: ratio = {1 + (cf.g('DYNAMIC_RATIO')/100.0)}")
        else:
            self.speech.dynamic_energy_adjustment_ratio =1.5  # reset to default
            LogInfo(f"SR Update: no dynamic, energy thresh={round(self.speech.energy_threshold)} x {1 + (cf.g('ENERGY_THRESH')/100.0)}")

        
        with sr.Microphone() as source:
            self.speech.adjust_for_ambient_noise(source, adjust_for_ambient)
            if not self.speech.dynamic_energy_threshold: self.speech.energy_threshold = self.speech.energy_threshold * (1 + (cf.g('ENERGY_THRESH')/100.0))
            LogInfo(f"SR Update: thresh = {round(self.speech.energy_threshold)}")

        return self.speech.current_energy

    def listen_thread(self, source, timeout):
        try:
            self.audio = self.speech.listen(source, timeout)
        except sr.exceptions.WaitTimeoutError:
            pass
        except sr.exceptions.UnknownValueError:
            pass
        except Exception as e:
            LogError(f"listen_thread error {str(e)}")


        
    def listen(self, beQuiet=False, time_out=cf.g('MIC_TO'), adjust_for_ambient=cf.g('AMBIENT')):
        imp = ""
        audio = False
        dt = datetime.now()
        self.speech.pause_threshold = cf.g('MIC_LIMIT')
        old_quiet = 0
        start_et = self.speech.energy_threshold

        with sr.Microphone() as source:
        #    self.speech.adjust_for_ambient_noise(source, adjust_for_ambient)
        #    self.speech.energy_threshold = self.speech.energy_threshold * 1.25

            if not beQuiet:
                self.start_mp3.play()
                pygame.time.wait(int(self.start_mp3.get_length() * 1000))
#                while pygame.mixer.music.get_busy(): sleep(0.1)
                if self.face: self.face.listening()
            try:
#                audio = self.speech.listen(source, timeout=5.0) #,dynamic_energy_threshold=False)
                self.audio = 0
                listen_thread = threading.Thread(target=self.listen_thread, args=(source, time_out))
                listen_thread.name = f"{GetHostname()} SR.listen_thread"
                listen_thread.start()
                run_avg = []
                x=0
                last_listen = datetime.now()
                LogDebug(f"Energy:\tCurr\tThrsh\tC-T\tAvg\tSecs")
                while listen_thread.is_alive():
                    x += 1
                    speaking_energy = round(self.speech.current_energy-self.speech.energy_threshold)
                    STATE.volume = self.speech.current_energy
                    run_avg.append(speaking_energy) # should be positive if user is speaking
                    if (x % 120) == 0: # print debug string every 1 secs
                        LogDebug(f"Energy:\t{round(self.speech.current_energy)}\t{round(self.speech.energy_threshold)}\t{speaking_energy}\t{round(sum(run_avg)/len(run_avg))}\t{(datetime.now()-dt).seconds}s")
                    if len(run_avg) == 120:
                        run_avg.pop(0) # only keep 1s frames at a time
                        if (datetime.now()-last_listen).seconds>cf.g('MIC_TO') or STATE.CheckState('Wake'): ## after this many secs, check if user is really talkiung
                            if (sum(run_avg)/len(run_avg))<0:
                                # they aren't talking, so start to jack up the threshold (limit to x4)
                                self.speech.energy_threshold=min(self.speech.energy_threshold*1.25, start_et*4)
                                run_avg.clear()
                            else: last_listen = datetime.now()
                    sleep(1/120)
            except Exception as e:
                #force the listen thread to stop
                while listen_thread.is_alive(): self.speech.energy_threshold=min(self.speech.energy_threshold*1.25, start_et*4)
                LogError(f"speech_listener.listener() returned error: {e.args}")
                self.audio = None  # don't try to use the mic again (was returned)

            if not beQuiet:
                if self.face: self.face.thinking()
                self.end_mp3.play()
            STATE.RevertWake()  # If Wake state while listening, user pushed button.  If not Wake State, this does nothing. 

            if self.audio:
                updt_thrd = self.update(asyn=True, needMic=False)
                try:
#                        imp = self.speech.recognize_google(audio)
                    imp = eval(f"self.recognize_{cf.g('INTERPRET_ENGINE')}(self.audio)")
                except sr.exceptions.UnknownValueError:
                    pass
                except Exception as e:
                    RaiseError(f"speech_listener.recognize_{cf.g('INTERPRET_ENGINE')}() returned error: {e.args}")
                    self.audio = ""
                self.audio=False
                while updt_thrd.is_alive(): sleep(0.25)

                #imp = self.engines['google')(audio)  ## NEEED FIX
            if imp:
                self.quiet = self.speech.current_energy  # retain the value from the update() call above.  This means it was quiet enough to hear
                LogInfo(f"Set Quiet to {self.quiet}.")
            LogConvo(f"{cf.g('USERNAME')}: '{imp}'  ({(datetime.now()-dt).seconds}s)")
                #self.speech.energy_threshold = start_et
            if self.face: self.face.off()
        return imp

    def Close(self):
        return

    def Evesdrop(self):
        return self.listen(True)
 
    ####### Engines in here

    def _recognize_default(self, audio):
        try:
            return self.speech.recognize_google(audio)
        except sr.RequestError as e:
            LogError("SR: Default (google) RequestError; {0}".format(e))
        return ""

    def recognize_vosk(self, audio):
        try:
            response =  self.speech.recognize_vosk(audio)
            d = json.loads(response)
            return d['text']

        except sr.RequestError as e:
            LogError("SR: google RequestError; {0}".format(e))
            return self._recognize_default(audio)


    def recognize_google(self, audio):
        try:
            return self.speech.recognize_google(audio)
        except sr.RequestError as e:
            LogError("SR: google RequestError; {0}".format(e))
            return self._recognize_default(audio)

    def recognizex_sphinx(self, audio):
        try:
            return self.speech.recognize_sphinx(audio)
        except sr.RequestError as e:
            LogError("Sphinx RequestError; {0}".format(e))
            return self._recognize_default(audio)

    def recognizex_google_api(self, audio):
        try:
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            if cf.g('GOOGLE_API'):
                self.speech.recognize_google(audio, key=cf.g('GOOGLE_API'))
            else:
                self.speech.recognize_google(audio)
        except sr.RequestError as e:
            LogError("Google Speech Recognition service RequestError; {0}".format(e))
            return self._recognize_default(audio)


    def recognizex_google_cloud(self, audio):
        try:
            self.speech.recognize_google(audio)
        except sr.RequestError as e:
            LogError("Google Speech Cloud Recognition service RequestError; {0}".format(e))
            return self._recognize_default(audio)

    def recognize_whisper(self, audio):
        resp = ""

        file_path = cf.g('WHISPER_WAV')
        with open(file_path, "wb") as file:
            file.write(audio.get_wav_data(convert_rate=16000, convert_width=2))

        try:
            ul_url = cf.g('WHISPER_URL')
            with open(file_path, 'rb') as f:
                files = {'file': f}

                data = {'response_format': 'json'}

                # Make the POST request
                try:
                    response = requests.post(ul_url, files=files, data=data, auth=(cf.g('USEREMAIL'), cf.g("WHISPER_API_KEY")))
                except sr.RequestError as e:
                    LogError(f"Whisper API Reqeust Error: {e}")
                    return self.speech.recognize_default(audio)

                # Print the response
                d = json.loads(response.text)
                resp = d['text'].replace("\n", " ")
            try: os.remove(filename)  # leave the file so it can be seen in logdebug
            except: pass

            # whisper will return sounds heard in ().  Exclaude these, but log them.
            newStr = ""
            action_str = ""
            exclude = False
            resp = resp.replace('[', '(')
            for s in resp:
                if not exclude and s == '(':
                    exclude = True
                    continue
                elif exclude and s == ')':
                    exclude = False
                    action_str  += ''
                    continue
                if not exclude:
                    newStr += s
                elif exclude: action_str += s

            if action_str: LogInfo(f"Heard action {action_str}")
            newStr = " ".join(newStr.split())
            return newStr.replace("  ", ' ') # join above did work for some reason?

        except Exception as e:
            LogError(f"Whisper API exception: {e}")
            return self._recognize_default(audio)

if __name__ == '__main__':
    pygame.mixer.init()
    sg = SpeechRecognition_listener()
    print("sg.update")
    sg.update()
#    sg.engine="whisper"
#    while True:
#        print("Can I hear you?", end="")
#        print(sg.CanIHearYou())
    txt = ""
    while txt.lower().replace(".", '') != 'quit':
        dt  = datetime.now()
#        print("Timeout: ", end="")
#        to = input()
#        print("Phrase Limit: ", end="")
#        pl = input()
#        cf.s('INTERPRET_ENGINE', 'vosk')
        print("Speak")
        txt = sg.listen()
        print(txt)
        print(f'\nElapsed Seconds: {(datetime.now()-dt).seconds}.  thrsh = {int(sg.speech.energy_threshold)}')
        sleep(1)
1
