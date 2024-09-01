#import pyttsx3
from datetime import datetime, timedelta
import warnings
from gtts import gTTS
#from playsound import playsound
#import pygobject
import pygame

class speech_generator:

    engine = 0
    last = 0

    def __init__(self):
#        self.engine = pyttsx3.init()
        pygame.mixer.init()
        return
    def say(self, txt):
        filename = "temp.mp3"
        if txt:
#            warnings.filterwarnings("ignore", category=DeprecationWarning)
#            self.engine.say (txt)    
#            self.engine.runAndWait()
#            self.engine.stop()
#            self.last = datetime.now()
            tts = gTTS(txt)
            tts.save(filename)
#            playsound(filename)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                continue
            print(f"AI: {txt}")
        return txt