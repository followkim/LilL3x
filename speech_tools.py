import pyttsx3
from gtts import gTTS
from openai import OpenAI
from time import sleep
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing

#from playsound import playsound
#import pygobject
import pygame
import warnings
from config import cf
from error_handling import RaiseError
from globals import STATE
import requests
voices = {}


class speech_generator:

    engine = 0
    last = 0
    volume = 0

    def __init__(self):
        pygame.mixer.init()
        self.engine = eval(cf.g('SPEECH_ENGINE')+'_tts()')
        # set Volume
        return

    def say(self, txt, leds):
#        if self.volume != config["VOLUME"]
#            set volume
        filename = "temp.mp3"
        if txt:
            try:
                leds.thinking()
                filename = self.engine.tts(txt)
                leds.talking()
                self.PlaySound(filename, True)
                print(f"AI: {txt}")
            except Exception as e:
                leds.off()
                return RaiseError("speech_tools:say error: " + str(e))
        leds.off()
        return txt

    def PlaySound(self, filename, watchState=False):
        if STATE.CheckState('Wake'): # if we start out in WAke, don't stop if we encouter it
            watchState = False
        if filename:
            pygame.mixer.music.set_volume(min(cf.g('VOLUME'), 10)/10) # does not go to 11
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if watchState and STATE.CheckState('Wake'):
                    pygame.mixer.music.stop()


    def StopSound(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        return not pygame.mixer.music.get_busy()

    def IsBusy(self):
        return pygame.mixer.music.get_busy()

    def SwitchEngine(self, engine_name=cf.g('SPEECH_ENGINE')):
        new_engine = 0
        new_engine = eval(engine_name+'_tts()')
        if new_engine:
            self.engine.Close()
            self.engine = new_engine
            return True
        else:
            print(f"Unable to switch to engine {engine}")
            return False

    def Close(self):
        pygame.quit()

class pytts_tts:
    engine = 0

    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', self.engine.getProperty('voices')[1].id)
        print("Speech Engine: pytts")
        return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
       self.engine.setProperty('volume', (min(cf.g('VOLUME'), 10)/10)) # does not go to 11
       self.engine.say(txt)
       self.engine.runAndWait()
       return False

    def Close(self):
        self.engine.stop()

class gTTS_tts:
    def __init__(self):
        print("Speech Engine: gTTS")
        return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        tts = gTTS(txt, lang='en', tld=cf.g('GTTS_VOICE'))
        tts.save(filename)
        return filename

    def Close(self):
        return

class ChatGPT_tts:
    client = 0
    def __init__(self):
        self.client = OpenAI(api_key=cf.g('OPEN_AI_API_KEY'))
        print("Speech Engine: ChatGPT")
        return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        with self.client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=cf.g('CHATGPT_VOICE'),
            input=txt
        ) as response:
            response.stream_to_file(filename)

        return filename

    def Close(self):
        return


class elevenLabs_tts:
    client = 0

    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + cf.g('ELEVENLABS_VOICE_ID')

    headers = {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": cf.g('ELEVENLABS_API_KEY')
    }

    def __init__(self):
#        self.client = El3venLabs(api_key=cf.g('ELEVENLABS_API_KEY'))
#        return self.client
         print("Speech Engine: ElevenLabs")
         return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        data = {
            "text": txt,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }

        response = requests.post(self.url, json=data, headers=self.headers)
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        return filename

    def Close(self):
        return

class amazon_tts:
    polly = 0
    session = 0
    def __init__(self):
         self.session = Session(
             aws_access_key_id = cf.g('AWS_ACCESS_KEY'),
             aws_secret_access_key= cf.g('AWS_ACCESS_KEY_SECRET'),
             region_name='us-west-2'
         )

         self.polly = self.session.client("polly")
         print("Speech Engine: Amazon AWS Polly")

         return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        try:
            # Request speech synthesis
            response = self.polly.synthesize_speech(Text=txt, OutputFormat="mp3", VoiceId="Joanna")
        except Exception as e:
            # The service returned an error, exit gracefully
            RaiseError(f"AWS returned error: {str(e)}")
            return False

        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
               try:
                # Open a file for writing the output as a binary stream
                    with open(filename, "wb") as file:
                       file.write(stream.read())
                       return filename
               except IOError as error:
                  # Could not write to file, exit gracefully
                  RaiseError(f"AWS returned error creating file: {str(e)}")
                  return False
        else:
            # The response didn't contain audio data, exit gracefully
            RaiseError(f"AWS returned error: {str(e)}")


    def Close(self):
       return

if __name__ == '__main__':
    class LEDS:
        def __init__(self):
             return
        def thinking(self):
             return
        def talking(self):
             return
        def off(self):
             return
    leds = LEDS()

    sr = speech_generator()
    sr.say("Hello world", leds)

    sr.SwitchEngine('pytts')
    sr.say("Hello world", leds)

