import pyttsx3
from gtts import gTTS
from openai import OpenAI
from time import sleep
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from google.cloud import texttospeech
from contextlib import closing

import pygame
import warnings
from config import cf
from error_handling import *
from globals import STATE, HasInternet
import requests
import re

from pydub import AudioSegment
from piper import PiperVoice
import wave

from typecast import Typecast
from typecast.models import TTSRequest, SmartPrompt, Output

LogInfo("Speech Engine Loading...")

def dummy():
    return

class DummySpeech:
    def __init__(self):pass
    def say(self, txt, face=False, asyn=False):
        print(txt)

class speech_generator:

    engine = 0
    engineName = ''
    last = 0
    volume = 0

    def __init__(self):
        self.engine_name = cf.g('SPEECH_ENGINE')
        self.engine = eval(self.engine_name+'_tts()')
      
        if HasInternet(): self.engine.tts(cf.g('ERROR_STR'), filename=cf.g('ERROR_FILE')) # generate the error file in the current voice
        return

    def say(self, txt, face=False, asyn=False, inFilename=cf.g('SPEECH_FILE')):
        if txt and re.search('[a-zA-Z0-9]', txt):
            filename = False
            if face: face.thinking()
            try:
                filename = self.engine.tts(txt, filename=inFilename)
            except Exception as e:
                LogError(f"{cf.g('SPEECH_ENGINE')} returned error: {e.args}, using gTTS")
            if not filename: filename = self.tts(txt) # play via gtts

            if face: face.talking()
            self.PlaySound(filename, watchState=True, asyn=asyn)
            LogConvo(f"{cf.g('AINAME')}: '{txt}'")

        elif not asyn: # in the case where the last file sent has no data but is not asyn
            if face: face.talking()
            while self.IsBusy(): sleep(0.25)
        if face and not asyn: face.off()
        return txt

    def PlaySound(self, filename, watchState=False, asyn=False):
        if STATE.CheckState('Wake'): watchState = False
        if filename:
            while pygame.mixer.get_busy(): sleep(0.5)
            s = pygame.mixer.Sound(filename)
            s.set_volume(min(cf.g('VOLUME'), 10)/10) # does not go to 11
            channel = s.play()
            while channel.get_busy() and not asyn:
                if watchState and STATE.CheckState('Wake'): s.stop()
                else: sleep(0.5) #STATE.volume = channel.get_volume()

    def StopSound(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        return not pygame.mixer.music.get_busy()

    def IsBusy(self):
        return pygame.mixer.get_busy()

    def SwitchEngine(self, engine_name=cf.g('SPEECH_ENGINE')):
        new_engine = 0
        try:
            new_engine = eval(engine_name+'_tts()')
        except Exception as e:
            LogError(f"Switch Engine caught exception {e.args}")

        if new_engine:
            self.engine.Close()
            self.engine = new_engine
            self.engine_name = engine_name
            self.engine.tts(cf.g('ERROR_STR'), filename=cf.g('ERROR_FILE'))
            cf.s('SPEECH_ENGINE', engine_name)
            return True
        else:
            LogWarn(f"SwitchEngine: Unable to switch to engine {engine_name}")

        cf.s('SPEECH_ENGINE', self.engine_name) # if we are here we weren't able to switch to the new engine.
        return False

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        try:
            tts = gTTS(txt, lang='en', tld=cf.g('GTTS_VOICE'))  # gTTS is the backup speech engine
            tts.save(filename)
            return filename
        except Exception as e:
            LogError(f"Backup speech failed {e.args}")
            return cf.g('ERROR_FILE')
    def Close(self):
        pygame.quit()

class pytts_tts:
    engine = 0

    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', self.engine.getProperty('voices')[1].id)
        LogInfo("Speech Engine: pytts")
        return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
       self.engine.setProperty('volume', (min(cf.g('VOLUME'), 10)/10)) # does not go to 11
       self.engine.save_to_file(txt, filename)
       self.engine.runAndWait()
       return filename

    def Close(self):
        self.engine.stop()

class gTTS_tts:
    def __init__(self):
        LogInfo("Speech Engine: gTTS")
        return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        tts = gTTS(txt, lang=cf.g('GTTS_LANG'), tld=cf.g('GTTS_VOICE'))
        tts.save(filename)
        return filename

    def Close(self):
        return

class ChatGPT_tts:
    client = 0
    def __init__(self):
        self.client = OpenAI(api_key=cf.g('OPEN_AI_API_KEY'))
        LogInfo("Speech Engine: ChatGPT")
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

    headers = {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": cf.g('ELEVENLABS_API_KEY')
    }

    def __init__(self):
         LogInfo("Speech Engine: ElevenLabs")
         return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        url = cf.g('ELEVENLABS_URL') + cf.g('ELEVENLABS_VOICE_ID')

        data = {
            "text": txt,
            "model_id": cf.g('ELEVENLABS_MODEL_ID'),
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }

        response = requests.post(url, json=data, headers=self.headers)
        if response.status_code != 200:
            LogDebug(response.json()['detail']['message'])
            LogError(f"elevenLabs_tts returned error {response.status_code} {response.json()['detail']['message']}")
            return False
        else:
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
         LogInfo("Speech Engine: Amazon AWS Polly")

         return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        try:
            # Request speech synthesis
            response = self.polly.synthesize_speech(Engine=cf.g('AWS_VOICE_ENGINE'), Text=txt, OutputFormat="mp3", VoiceId=cf.g('AWS_VOICE_ID'))
        except Exception as e:
            # The service returned an error, exit gracefully
            LogError(f"AWS returned error: {e.args}")
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
                  LogError(f"AWS returned IO error")
               except Exception as e:
                  LogError(f"AWS returned IO error creating file: {e.args}")
                  return False
        else:
            # The response didn't contain audio data, exit gracefully
            LogError(f"AWS returned error: No audio Stream")
            return False

    def Close(self):
       return

class google_tts:
    client = 0
    config = 0
    voice = 0 
    lang_code = ''
    voice_name = ''
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient(client_options={"api_key": cf.g('GOOGLE_CLOUD_API')})

        self.config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        self.voice = self.init_voice()

    def init_voice(self):
        voice = texttospeech.VoiceSelectionParams(
            language_code=cf.g('GOOGLE_LANG_CODE'),
            name=cf.g('GOOGLE_VOICE_NAME'),
            ssml_gender=eval(f"texttospeech.SsmlVoiceGender.{cf.g('GOOGLE_GENDER').upper()}")
        )
        self.lang_code = cf.g('GOOGLE_LANG_CODE')
        self.voice_name = cf.g('GOOGLE_VOICE_NAME')
        return voice


    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        if self.lang_code != cf.g('GOOGLE_LANG_CODE') or self.voice_name != cf.g('GOOGLE_VOICE_NAME'): self.voice = self.init_voice()

        try:
            sinput = texttospeech.SynthesisInput(text=txt)
            response = self.client.synthesize_speech(input=sinput, voice=self.voice, audio_config=self.config)
        except Exception as e:
            LogError(f"Google_tts caught error synthesizing speech: {str(e)}")
            return False

        try:
            with open(filename, 'wb') as out:
                # Write the response to the output file.
                out.write(response.audio_content)
                return filename
        except Exception as e:
            LogError(f"Google_tts caught error writing to file: {str(e)}")

        return False

    def Close(self):
        return

class typeCast_tts:
    client = 0

    def __init__(self):
         LogInfo("Speech Engine: TypeCast")
         self.client = Typecast(api_key = cf.g('TYPECAST_API_KEY'))
         return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        response = None
        try:
            response = self.client.text_to_speech(TTSRequest(
                text = txt,
                model = cf.g('TYPECAST_MODEL'),
                voice_id = cf.g('TYPECAST_VOICE_ID'),
                output=Output(audio_format="mp3")
            ))
        except Exception as e:
             LogError(f"TypeCast Error:{e.args}")
             return False
#        if response.status_code != 200:
#            LogError(f"typeCast_tts returned error {response.status_code} - {response.text}")
#            return False

        with open(filename, 'wb') as f:
            f.write(response.audio_data)
        return filename

    def Close(self):
        return

class piper_tts:

    voice = False
    def __init__(self):
        LogWarn("Loading Piper... NOTE SYSTEM WILL FREEZE MOMENTARILY!")
        self.voice = PiperVoice.load(cf.g('PIPER_VOICE'))
        LogInfo("Speech Engine: Piper")
        return

    def tts(self, txt, filename=cf.g('SPEECH_FILE')):
        with wave.open("./temp/piper.wav", "wb") as wav_file:
            self.voice.synthesize_wav(txt, wav_file)
        audio = AudioSegment.from_wav("./temp/piper.wav")
        audio.export(filename, format="mp3")
        return filename

    def Close(self):
        return


if __name__ == '__main__':

    pygame.mixer.init()
    sr = speech_generator()


    sr.say("Alexander Hamilton", asyn=False)
    sr.say("My name is Alexander Hamilton", asyn=True)
    sr.say("And there's a million things I haven't done", asyn=True)
    sr.say("But just you wait, just you wait", asyn=False)

    print("done")
