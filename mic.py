import speech_recognition as sr

# Replace 'YOUR_DEVICE_INDEX' with the actual index obtained from step 1
device_index = 0

r = sr.Recognizer()
r.energy_threshold = 1000
r.pause_threshold = 0.5
r.phrase_time_limit =0.5

with sr.Microphone(device_index=device_index) as source:
    print("Say something!")
    audio = r.listen(source)

try:
    print("You said: " + r.recognize_google(audio))
except sr.UnknownValueError:
    print("Speech Recognition could not understand audio")
except sr.RequestError as e:
    print(f"Could not request results from Google Speech Recognition service; {e}")
