import re
from trieregex import TrieRegEx as TRE
import warnings
import sounddevice as sd
from datetime import datetime, timedelta
from time import sleep
import pygame
import json
import threading
from globals import MIC_STATE, STATE
from config import cf
from error_handling import *
from vosk import Model, KaldiRecognizer
import queue

AUDIO_DEVICE = None

q = queue.Queue()

LogInfo("Importing Vosk Wake...")

def callback(indata, frames, time, status):
    if status: print(status)
    q.put(bytes(indata))

class Vosk_listener:

    rec = 0
    engine = 0
    samplerate=0
    start_mp3 = 0
    end_mp3 = 0
    wake_mp3 = 0
    is_speaking=False
    face = 0
    wake_phrase = ""
    should_quit = False

    def __init__(self, face):

        device_info = sd.query_devices(AUDIO_DEVICE, "input")
        self.samplerate = int(device_info["default_samplerate"])
        model = Model(lang="en-us")

        self.rec = KaldiRecognizer(model, self.samplerate)
        self.wake_mp3 = pygame.mixer.Sound(cf.g('WAKE_MP3'))
        self.face = face
        self.start_mp3 = pygame.mixer.Sound(cf.g('START_LISTEN_MP3'))
        self.end_mp3 = pygame.mixer.Sound(cf.g('END_LISTEN_MP3'))

    def update(self, asyn=False, needMic=True):
         return

    def clear(self):
         while not q.empty(): q.get()

    def Evesdrop(self):
        return self.listen(beQuiet=True)

    def CanIHearYou(self, dur=30):
        return self.listen(True, time_out=dur) != ""

    def ww_thread(self):
        stream = 0
        regex = re.compile(f"\\b{cf.g('WAKE_WORD_REGEX')}\\b")
        while (not self.should_quit):
            if not STATE.IsInteractive() and MIC_STATE.TakeMic(False):
                while not q.empty(): q.get()  # empty the q
                self.is_speaking = False
                stream = sd.RawInputStream(samplerate=self.samplerate, blocksize = 8000, device=AUDIO_DEVICE, dtype="int16", channels=1, callback=callback)
                with stream:
                    input = ""
                    will_wake = False
                    while (not MIC_STATE.MicRequested() and not STATE.CheckState('Quit') and not STATE.IsInteractive()):
                        data = q.get()
                        if self.rec.AcceptWaveform(data):
                            jt = json.loads(self.rec.Result())
                            if will_wake or re.search(regex, jt["text"].lower()):
                                input = jt["text"]
                                match = re.findall(regex, input.lower())
                                if match: input = input.lower().replace(match[0][0], cf.g('AINAMEP'))
                                self.wake_phrase = input.strip()
                                LogConvo(f"{cf.g('USERNAME')}: {self.wake_phrase}") 
                                STATE.ChangeState("Wake")
                            elif len(jt['text'])>0 and jt['text'] != 'huh':
                                LogDebug(f"WW: heard '{jt['text']}'")
                            self.is_speaking=False
                        elif self.rec.PartialResult():
                            pr = self.rec.PartialResult()
                            self.is_speaking=True
                            if not will_wake and re.search(regex, pr.lower()):
                                self.wake_mp3.play()
                                will_wake = True
                                self.face.listening()

                while not q.empty(): q.get()  # empty the q
                self.face.off()
                stream.close()
                MIC_STATE.last = datetime.now()
                MIC_STATE.ReturnMic()
                sleep(5) # give tiuem to give up mic
            else: sleep(2)

    def Close(self):
        self.should_quit = True
        return




    def listen(self, beQuiet=False, time_out=cf.g('MIC_TO'), adjust_for_ambient=cf.g('AMBIENT')):

        input = ""
        stream = 0
        dt = datetime.now()
        if (MIC_STATE.CanUse()): MIC_STATE.TakeMic()
        self.clear()
        try:
            stream = sd.RawInputStream(samplerate=self.samplerate, blocksize = 8000, device=AUDIO_DEVICE, dtype="int16", channels=1, callback=callback)
            with stream:
                if not beQuiet: 
                    self.start_mp3.play()
                    if self.face: self.face.listening()
                last_listen = datetime.now()

                while input=="" and  (datetime.now()-last_listen).seconds < time_out:
                    data = q.get() #blocking
                    if self.rec.AcceptWaveform(data):
                        jt = json.loads(self.rec.Result())
                        if len(jt['text'])>0 and jt['text'] != 'huh':
                            input = jt["text"].strip()
                            if not beQuiet: 
                                self.start_mp3.play()
                                if self.face: self.face.off()

                    elif self.rec.PartialResult():
                        pr = json.loads(self.rec.PartialResult())
                        if pr['partial'] not in ("", "huh"):
                            LogDebug(f"Listen Partial: {pr['partial']}")
                            last_listen = datetime.now()
        except Exception as e:
            LogError(f"Vosk: Listen caught exception {e.args}")
        # empty the Q
        self.clear()
        stream.close()
        if self.face: self.face.off()
        LogConvo(f"{cf.g('USERNAME')}: '{input}'  ({(datetime.now()-dt).seconds}s)")
        MIC_STATE.ReturnMic()
        return input

    def Close(self):
        return

    def GetWakePhrase(self):
        wp = self.wake_phrase
        self.wake_phrase = ""
        return wp

    def TrainWakeWord(self):
        success = 0
        tries = 0
        words = []
        regex = cf.g('WAKE_WORD_REGEX')
        while success < cf.g('WAKE_WORD_TRIES') and tries < cf.g('WAKE_WORD_TRIES')*2:
            word = self.listen()  #TODO
            if word:
                LogDebug(f"Heard: {word}")
                if word in ('quit', 'stop', 'goodbye', 'end'): break
                if not word in words: words.append(word)

                tre = TRE(*words)  # word(s) can be added upon instance
                new_regex = tre.regex()
                if new_regex:
                   LogDebug(f"regex: '{regex}'")
                   regex=new_regex
                else: printf(f"Got Blank regex: {words}")
                regexc = re.compile(f'\\b{regex}\\b')
                if regexc.match(word): success = success + 1
                else: tries = tries+1
            else: tries = tries+1
        if success >= cf.g('WAKE_WORD_TRIES'): cf.s('WAKE_WORD_REGEX', regex)
        return (tries<cf.g('WAKE_WORD_TRIES')*2)

if __name__ == '__main__':
    from face import DummyFace, Face
    pygame.mixer.init()
    face = DummyFace()
    sg = Vosk_listener(face)
#    print("setting ambient")
#    sg.update(5)
    STATE.ChangeState('Active')
#    sg.engine="whisper"
#    while True:
#        print("Can I hear you?", end="")
#        print(sg.CanIHearYou())

    sg.TrainWakeWord()    

    txt = "quit"
    while txt != 'quit':
        STATE.ChangeState('Active')
        dt  = datetime.now()
        
        thread = threading.Thread(target=sg.ww_thread)
        thread.start()        
        while not STATE.CheckState('Wake'):
            sleep(0.5)
        print("wake phrase: " + sg.wake_phrase)
        print(f'\nElapsed Seconds: {(datetime.now()-dt).seconds}')

