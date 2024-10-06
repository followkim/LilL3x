import re
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
        while (not STATE.CheckState('Quit')):
            if not STATE.IsInteractive() and MIC_STATE.TakeMic(False):
                while not q.empty(): q.get()  # empty the q
                stream = sd.RawInputStream(samplerate=self.samplerate, blocksize = 8000, device=AUDIO_DEVICE, dtype="int16", channels=1, callback=callback)
                with stream:
                    input = ""
                    will_wake = False
                    while (not MIC_STATE.MicRequested() and not STATE.CheckState('Quit') and not STATE.IsInteractive()) or not q.empty():
                        data = q.get()
                        if self.rec.AcceptWaveform(data):
                            jt = json.loads(self.rec.Result())
                            if will_wake or re.search("(ele(k|c)tr(a|ic)|alexis)", jt["text"].lower()):
                                input = jt["text"]
                                match = re.findall("(ele(k|c)tr(a|ic)|alexis|lecturn)", input.lower())
                                if match: input = input.lower().replace(match[0][0], cf.g('AINAME'))
                                self.wake_phrase = input.strip()
                                LogConvo(f"{cf.g('USERNAME')}: {self.wake_phrase}") 
                                STATE.ChangeState("Wake")
                                while not q.empty(): q.get()  # empty the q
                            else: 
                                LogDebug(f"WW: heard '{jt['text']}'")
                            self.is_speaking=False
                        elif self.rec.PartialResult():
                            pr = self.rec.PartialResult()
                            self.is_speaking=True
                            if not will_wake and re.search("(ele(k|c)tr(a|ic)|alexis)", pr.lower()):
                                self.wake_mp3.play()
                                will_wake = True
                                self.face.listening()

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

