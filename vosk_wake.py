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
    q.put(bytes(indata))

class vosk_wake:

    rec = 0
    engine = 0
    samplerate=0
    wake_mp3 = 0  
    is_speaking=False
    face = 0
    wake_phrase = ""

    def __init__(self, face):
        device_info = sd.query_devices(AUDIO_DEVICE, "input")
        # soundfile expects an int, sounddevice provides a float:
        self.samplerate = int(device_info["default_samplerate"])
        model = Model(lang="en-us")
        self.rec = KaldiRecognizer(model, self.samplerate)
        self.wake_mp3 = pygame.mixer.Sound(cf.g('WAKE_MP3'))
        self.face = face
        return

    def listen(self):
        stream = 0
        regex = cf.g('WAKE_REGEX').replace('`', '|')
        while (not STATE.CheckState('Quit')):
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
                MIC_STATE.last = datetime.now()
                MIC_STATE.ReturnMic()
                stream.close()
                sleep(5) # give tiuem to give up mic
            else: sleep(2)
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
        regex = cf.g('WAKE_REGEX').replace('`', '|')
        while success < cf.g('WAKE_WORD_TRIES') and tries < cf.g('WAKE_WORD_TRIES')*2:
            word = input("Word: ").lower()  #TODO
            if word in ('quit', 'stop', 'goodbye', 'end'): break
            if not word in words: words.append(word)
            tre = TRE(*words)  # word(s) can be added upon instance
            regex = tre.regex()
            LogDebug(f"regex: {regex}")

            regexc = re.compile(f'\\b{regex}\\b')
            if regexc.match(word): success = success + 1
            else: tries = tries+1
        if success >= cf.g('WAKE_WORD_TRIES'): cf.s('WAKE_REGEX', regex).replace('|', '`')
        return (tries<cf.g('WAKE_WORD_TRIES')*2)

if __name__ == '__main__':
    pygame.mixer.init()
    sg = vosk_wake()
#    print("setting ambient")
#    sg.update(5)
    STATE.ChangeState('Active')
#    sg.engine="whisper"
#    while True:
#        print("Can I hear you?", end="")
#        print(sg.CanIHearYou())
    txt = ""
    while txt != 'quit':
        STATE.ChangeState('Active')
        dt  = datetime.now()
        
        thread = threading.Thread(target=sg.listen)
        thread.start()        
        while not STATE.CheckState('Wake'):
            sleep(0.5)
        print("wake phrase: " + sg.wake_phrase)
        print(f'\nElapsed Seconds: {(datetime.now()-dt).seconds}')

