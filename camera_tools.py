from picamera2 import Picamera2
from picamera2.outputs import FileOutput
import cv2
import requests
import base64
from gpiozero import CPUTemperature
import pygame

from time import sleep
from datetime import datetime
from  error_handling import *
import os
import shutil
from datetime import datetime, timedelta
import numpy
import time
import threading
from globals import STATE
from config import cf
#from speech_tools import PlaySound
from deepface import DeepFace
import re

LogInfo("Camera Loading...")

class Camera:
    cam = None
    shutter = 0
    last_seen = datetime.now() 
    last_motion = datetime.now()
    is_dark = False
    face_cascade = 0
    eye_cascade = 0
    show_view = False
    take_picture = False
    be_quiet = False
    mood=""

    def __init__(self):
        try:

            os.environ["LIBCAMERA_LOG_LEVELS"] = "3"
            self.cam = Picamera2()
            video_config = self.cam.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"},
                                                 lores={"size": (320,240), "format": "YUV420"})
            self.cam.configure(video_config)
            self.shutter = pygame.mixer.Sound(cf.g('CAMERA_CLICK_MP3'))

            # see https://www.geeksforgeeks.org/opencv-python-program-face-detection/
            # https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml 
            haarFolder = './haarcascades/'
            self.face_cascade = cv2.CascadeClassifier(haarFolder + 'haarcascade_frontalface_default.xml') 
            self.eye_cascade = cv2.CascadeClassifier(haarFolder + 'haarcascade_eye.xml') 

            self.cam.start()

        except Exception as e:
            RaiseError(f"Unable to init Picamera: {str(e)}")
            self.cam = False
        return
    
    def CameraLoopThread(self):
        self._camera_loop_thread()
               

    def _camera_loop_thread(self):
        tracker = False
        prev = None
        dt=datetime.now()
        mood_thrd = threading.Thread(target=self._get_emotion_thread)

        while not STATE.CheckState('Quit') and self.cam:
            if CPUTemperature().temperature >= cf.g('CPU_MAX_TEMP'):
                RaiseError(f"Camera not used: CPU too hot ({CPUTemperature().temperature})")
                self.cam.stop()
                while CPUTemperature().temperature >= cf.g('CPU_MAX_TEMP')-(cf.g('CPU_MAX_TEMP')/10):
                    sleep(60)
                self.cam.start()
                continue

            img = self._read_camera_array()
            if isinstance(img, bool):
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if tracker:
                success,bbox=tracker.update(img)
                if success: 
                    (x, y, w, h) = bbox
                    tries = 0
                    success = False
                    while tries < 5 and not success:
                        eyes = self.eye_cascade.detectMultiScale(gray[int(y):int(y+h), int(x):int(x+w)])
                        if len(eyes) > 0:
                            self.last_seen = datetime.now()
                            STATE.cx = 1280 - ((w//2) + x)
                            STATE.cy = (h//2) + y
                            LogDebug(f"Tracking: x={round(STATE.cx)}, y={round(STATE.cy)}")
                            cv2.rectangle(img,(int(x),int(y)),(int(x+w),int(y+h)),(0,0,0),10)
                            success = True
                        else: tries = tries+1

                if not success: # lost face
                    LogDebug("Camera: Lost face")
                    tracker = False
                    STATE.cx=-1
                    STATE.cy=-1
                    
            if tracker == False:  # don't use an else as tracker might ahve turned false above
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces)>0:
                    for (x, y, w, h) in faces:
                        eyes = self.eye_cascade.detectMultiScale(gray[int(y):int(y+h), int(x):int(x+w)])
                        if len(eyes) > 0:
                            self.last_seen = datetime.now()
                            #tracker=cv2.legacy.TrackerMedianFlow_create()
                            #tracker=cv2.legacy.TrackerKCF_create()
                            #tracker=cv2.legacy.TrackerMOSSE_create()
                            tracker=cv2.legacy.TrackerCSRT_create()
                            ret = tracker.init(img, (x, y, w, h))
                else:
                    tracker = False
                    STATE.cx=-1
                    STATE.cy=-1
                    tracking_frames = 0
            prev = self._detect_motion(img, prev)
            self._is_dark(img)
            # perform camera requests
            if tracker and not mood_thrd.is_alive():  # get the mood
                mood_thrd = threading.Thread(target=self._get_emotion_thread, args=(img,))
                mood_thrd.start()
            if self.show_view: self._whatISee(img)
            if self.take_picture: self._take_picture(image=img, filename=self.take_picture, beQuiet=self.be_quiet)
#            if self._is_dark(): sleep(30) # don't check for dark if there is movement
            if not tracker: sleep(max((1/cf.g('FPS')) - (datetime.now()-dt).microseconds/1000000, 0))


        if self.cam: self.cam.stop()

    def _read_camera_buffer(self):
        try:
            return cv2.flip(self.cam.capture_buffer("lores"), 0)
        except Exception as e:
            return RaiseError(f"Error reading camera ({str(e)})")

    def _read_camera_array(self):
        try:
            return cv2.flip(self.cam.capture_array(), 0)
        except Exception as e:
            return RaiseError(f"Error reading camera ({str(e)})")


    def IsDark(self):
        return self.is_dark
    
    def _is_dark(self, image):
        # Convert image to HSV colorspace
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Extract the V channel (Value channel represents brightness)
        v_channel = hsv[:, :, 2]
        brightness = numpy.mean(v_channel)
        self.is_dark= brightness<=cf.g('IS_DARK_THRESH')
        return self.is_dark

    def CanISeeYou(self, secs=cf.g('LOOK_SECS_TO_DEFAULT')):
        return self.last_seen > (datetime.now() - timedelta(seconds=secs))

    # Note: _look_for_user assumes OPEN cameara instance.
    #https://github.com/raspberrypi/picamera2/blob/main/examples/capture_motion.py
    def IsUserMoving(self, secs=cf.g('LOOK_SECS_TO_DEFAULT')):
        return max(self.last_seen, self.last_motion) > datetime.now() - timedelta(seconds=secs)


    def _detect_motion(self, cur, prev=None):
        if prev is not None:
            try:
                mse = numpy.square(numpy.subtract(cur, prev)).mean()
            except Exception as e: 
                return LogDebug("_detect motion exptn: {str(e)}")
            if mse > cf.g('MOTDET_SENS'):
                self.last_motion = datetime.now()
#        return icu>=cf.g('MOTDET_THRESH')
        return cur # allows easy setting of previous frame

    def ShowView(self):
        self.show_view=True

    def EndShowView(self):
        self._show_view = False
        sleep(0.25)
        try: os.remove('.frames/wis.ppm')
        except: pass
        return

    def _whatISee(self, img=False):
        if isinstance(img, bool): img = self._read_camera_buffer()
#        self._take_picture("./frames/wis.jpg", beQuiet=True)
#        jpg = cv2.imread('./frames/wis.jpg')
        gmi = cv2.flip(img, 1)
        ig = cv2.resize(gmi, (128, 64))
        cv2.imwrite('./frames/wis.ppm', ig)

    def TakePicture(self, fname=cf.g('TEMP_PATH_DEFAULT'), beQuiet=False):
        if is_dir(fname):
            filename = fname+'capture_'+datetime.now().strftime(cf.g('SFT_FORMAT')) +'.jpg'
        else:
            filename = fname
        self.take_picture = filename
        self.be_quiet = beQuiet
        cnt = 0
        while (not os.path.isfile(filename)) and cnt<8: # 2 sec
            sleep(0.25)
            cnt = cnt+1   # just in case the file never materializes
        if cnt<8: return filename
        return False

    def _take_picture(self, image, filename=cf.g('TEMP_PATH_DEFAULT'), beQuiet=False):
        print(f"Called _TAKE_PICTURE({filename}, {beQuiet}")
        try:
            if isinstance(image, bool): self.cam.capture_file(filename)
            else: cv2.imwrite(filename, image)
            LogDebug(f"_take_picture: '{filename}'")
            # show the image for 3 secs and play a shutter sound
            if not beQuiet:
                self.shutter.play()
                sleep(cf.g('CAMERA_PICT_SEC'))
            self.take_picture = False
            return filename
        except Exception as e:
            LogError(f"_take_picture: Couldn't take pict '{filename}': {str(e)}")
            return False
    
    def SendPicture(self):
        path = self.TakePicture()
        if path:
            cnt = 0
            return self.UploadPicture(path)

    def UploadPicture(self, pict_path):
        url = False
        if pict_path and os.path.isfile(pict_path):
            ul_url = 'http://el3ktra.el3ktra.net/upload.php'
            files={'fileToUpload': open(pict_path,'rb')}
            payload = {'submit': 'Upload Image'}
            r = requests.post(ul_url, data=payload, files=files)
            url = r.text
        return url

    def SharePicture(self):
        fname = self.TakePicture()
        url = self.UploadPicture(fname) 
        print(f"fname:{fname}")
        print(f"url:{url}")
        return url

    def GetEmotion(self):
        ret = self.mood
        self.mood = ""
        return ret

    def _get_emotion_thread(self, image=False, filename=cf.g('TEMP_PATH_DEFAULT')+'mood.jpg'):
        LogDebug("_get_emotion_thread called")
        self.mood = ""
        if isinstance(image, bool): imagePath = self.TakePicture(filename, beQuiet=True)
        else: cv2.imwrite(filename, image)
        try:
            objs = DeepFace.analyze(img_path=filename,  actions = ['emotion'])
            if objs: self.mood = objs[0]['dominant_emotion']
        except:
            pass
        if self.mood=="neutral": self.mood=""

        try: os.remove(filename)
        except: pass

        sleep(5*60)  # don't call more then ev ery 5 minutes
        self.mood = ""    # assume that whatever they were feeling is past

    def WhoAmI(self):
        user_img = self.TakePicture(seeUser=True, beQuiet=True)
        if user_img:
           try:
               dfs = DeepFace.find(img_path=user_img, db_path="people/")
               LogDebug(str(dfs))
           except: 
               pass
        return
    
    def Close(self):
        return

def is_dir(path):
    return path[-1] == '/'


if __name__ == '__main__':
    global STATE

    pygame.mixer.init()
    STATE.ChangeState('Idle')
    c = Camera()
#    exit(0)
    try: 
        c.show_view=True
        Thread  = threading.Thread(target=c.CameraLoopThread)
        Thread.start()
        sleep(10)
#    print(c.SharePicture())
        x = 0
        while x < 100: 
            print(c.CanISeeYou())
            print(f'last motion: {c.last_motion.strftime("%H:%M:%S")}')
            print(f'last seen: {c.last_seen.strftime("%H:%M:%S")}')
            print(f'mood: {c.GetEmotion()}')
            print(f'is_dark: {c.is_dark}\n\n')
            sleep(5)
            x=x+1
    #    sleep(120)
        STATE.ChangeState('Quit')
        sleep(2)
    except:
        exit(0)
