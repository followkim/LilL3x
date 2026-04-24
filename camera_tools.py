from picamera2 import Picamera2
from picamera2.outputs import FileOutput
import cv2
import requests
import base64
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
from globals import STATE, SleepOn, GetIP
from config import cf
#from speech_tools import PlaySound
#from deepface import DeepFace
import re
import pyimgur

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
    take_portrait = False
    be_quiet = False
    mood=""
    should_quit = False
    cam_thread = False
    def __init__(self):
        try:

            self.shutter = pygame.mixer.Sound(cf.g('CAMERA_CLICK_MP3'))

            # see https://www.geeksforgeeks.org/opencv-python-program-face-detection/
            # https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml 
            haarFolder = './haarcascades/'
            self.face_cascade = cv2.CascadeClassifier(haarFolder + 'haarcascade_frontalface_default.xml') 
            self.eye_cascade = cv2.CascadeClassifier(haarFolder + 'haarcascade_eye.xml') 

            self.cam = Picamera2()
            video_config = self.cam.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"}, lores={"size": (320,240), "format": "YUV420"})
            self.cam.configure(video_config)

            self.CheckCameraThread()

        except Exception as e:
            RaiseError(f"Camera() exception in __init__: {e.args}")
            self.cam = False
        return

    def CheckCameraThread(self):
        if not self.CameraAlive():
            self.cam_thread = threading.Thread(target=self._camera_loop_thread, daemon=True)
            self.cam_thread.name = f"{GetHostname()} CameraLoopThread"
            self.cam_thread.start()

    def CameraAlive(self):
        return self.cam_thread and self.cam_thread.is_alive()

    def _camera_loop_thread(self):
        tracker = None
        prev = None
        dt=datetime.now()
#        mood_thrd = threading.Thread(target=self._get_emotion_thread)  # need to init here to call "is_alive" later

        # open the camera
        try: 
            os.environ["LIBCAMERA_LOG_LEVELS"] = "3"
            self.cam.start()
        except Exception as e:
            RaiseError(f"Unable to init Picamera: {e.args}")
            self.cam = None

        LogInfo("Camera thread starting.")
        while not STATE.ShouldQuit() and not self.should_quit and self.cam:
             try:
                if STATE.temp >= cf.g('CPU_MAX_TEMP'):
                    LogError(f"Camera not used: CPU too hot ({STATE.temp})")
                    self.cam.stop()
                    while STATE.temp >= cf.g('CPU_MAX_TEMP')-(cf.g('CPU_MAX_TEMP')/10):
                        sleep(60)  # force sleep
                    self.cam.start()
                    continue

                # do not use the camera if in Active or Wake... unless asked to.  should_wake() is true if user asks for camera.
                if self.should_wake() or not STATE.IsInteractive():
                    img = self.__read_camera_array()
                    if isinstance(img, bool):  #__is_dark will access image.  Don't do anything if there isn't an image
                        LogError(f"Unable to get camera  image")
                        SleepOn(cf.g('CAMERA_SLEEP_SEC')*2)
                        continue

                    if self.__is_dark(img):
                        STATE.ChangeState('SleepState')      # allow the camera to dictate this, LilLex.Sleep() will reset state when light again
                        SleepOn(secs=cf.g('CAMERA_SLEEP_SEC')*2, varf=STATE.IsSleeping, wakeOn=False)
                        continue                             # as it is dark, we can't see anything and should try to continue loop

                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                     # Handle Tracker
                    if tracker:
                        success,bbox=tracker.update(img)
                        if success and min(bbox[2], bbox[3]) > cf.g('MIN_FACE_SIZE'):
                            (x, y, w, h) = bbox
                            eyes = self.eye_cascade.detectMultiScale(gray[int(y):int(y+h), int(x):int(x+w)])
                            if len(eyes) > 0:
                                self.last_seen = datetime.now()
                                STATE.cx = int((w//2) + x)
                                STATE.cy = int((h//2) + y)
                                if cf.g('SCREEN_DEBUG') and self.show_view: cv2.rectangle(img,(int(x),int(y)),(int(x+w),int(y+h)),(0,0,0),10)

                                if self.take_portrait:
                                    self._take_picture(image=img, filename=self.take_portrait, beQuiet=self.be_quiet, seeUser=True)
                                success = True
                            else: success = False

                        if not success: # lost face
                            tracker = None
                            STATE.cx=0
                            STATE.cy=0
                            
                    if not tracker:  # don't use an else as tracker might ahve turned false above
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
                                    if cf.g('SCREEN_DEBUG') and self.show_view: cv2.rectangle(img,(int(x),int(y)),(int(x+w),int(y+h)),(0,0,0),10)
#                                    LogDebug(f"Camera: Found Face at ({x}, {y}, {w}, {h})")
                        else:
                            tracker = None
                            STATE.cx=0
                            STATE.cy=0
                    #end Tracker

                    prev = self._detect_motion(img, prev)

                    # perform camera requests
                    '''  This code doesn't seem to work  - always thinks I'm pissed
                    if tracker and not mood_thrd.is_alive():  # get the mood
                        mood_thrd = threading.Thread(target=self._get_emotion_thread, args=(img,), daemon=True)
                        mood_thrd.name = f"{GetHostname()} GetEmotionThread"
                        mood_thrd.start()
                    '''
                    if self.show_view: self._whatISee(img)
                    if self.take_picture: self._take_picture(image=img, filename=self.take_picture, beQuiet=self.be_quiet)
                # END if should_wake or not.STATEIsInteractive()

                #sleep the camera
                if self.should_wake(): pass # don't sleep if there is a request
                elif tracker: sleep(max((1/cf.g('FPS')) - (datetime.now()-dt).microseconds/1000000, 0)) # match screen FPS.  Too short to use SleepOn
                else: SleepOn(cf.g('CAMERA_SLEEP_SEC'), self.should_wake, 0.25, watchState=False, wakeOn=True)  # want to limit sleep to check for tracking
             except Exception as e:
                  LogError(f"CameraLoop Uncaught Exception {e.args}")
        if self.cam: self.cam.stop()
        LogInfo("Camera thread exiting.")
        STATE.cx=0
        STATE.cy=0

    def should_wake(self):
          return self.show_view or self.take_picture or self.take_portrait

    def __read_camera_buffer(self):
        try:
            return cv2.flip(self.cam.capture_buffer("lores"), 0)
        except Exception as e:
            return RaiseError(f"Error reading camera ({e.args})")

    def __read_camera_array(self):
        try:
            return cv2.flip(self.cam.capture_array(), 0)
        except Exception as e:
            return RaiseError(f"Error reading camera ({e.args})")

    def IsDark(self):
        return self.is_dark
    
    def __is_dark(self, image):
        # Convert image to HSV colorspace
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Extract the V channel (Value channel represents brightness)
        v_channel = hsv[:, :, 2]
        brightness = numpy.mean(v_channel)

        oldDark = self.is_dark
        self.is_dark = brightness<=cf.g('IS_DARK_THRESH')
        if oldDark != self.is_dark: LogDebug(f"is_dark changed to {self.is_dark}: (brightness={round(brightness)})")
        return self.is_dark

    def CanISeeYou(self, secs=cf.g('LOOK_SECS_TO_DEFAULT')):
        self.CheckCameraThread()
        return self.last_seen > (datetime.now() - timedelta(seconds=secs))

    def LastSeen(self):
        self.CheckCameraThread()
        return (datetime.now()-self.last_seen).total_seconds()

    # Note: _look_for_user assumes OPEN cameara instance.
    #https://github.com/raspberrypi/picamera2/blob/main/examples/capture_motion.py
    def IsUserMoving(self, secs=cf.g('LOOK_SECS_TO_DEFAULT')):
        self.CheckCameraThread()
        return max(self.last_seen, self.last_motion) > datetime.now() - timedelta(seconds=secs)


    def _detect_motion(self, cur, prev=None):
        if prev is not None:
            try:
                mse = numpy.square(numpy.subtract(cur, prev)).mean()
            except Exception as e: 
                return LogError("_detect motion exptn: {e.args}")
            if mse > cf.g('MOTDET_SENS'):
                self.last_motion = datetime.now()
#        return icu>=cf.g('MOTDET_THRESH')
        return cur # allows easy setting of previous frame

    def ShowView(self):
        self.CheckCameraThread()
        if not self.show_view: RemoveFile(cf.g('WIS_FILE'))  #remove view file if exsists
        self.show_view=True

    def EndShowView(self):
        self.show_view = False
        sleep(0.25) # wait for file to be shown
        RemoveFile(cf.g('WIS_FILE'))
        return

    def _whatISee(self, img=False, filename=cf.g('WIS_FILE')):
        if isinstance(img, bool): img = self.__read_camera_buffer()

#        gmi = cv2.flip(img, 1)
        ig = cv2.resize(img, (128, 64))

        temp = filename.replace('.ppm', '_temp.ppm')
        cv2.imwrite(temp, ig)
        os.rename(temp, filename)

    def TakePortrait(self, fname=cf.g('PICT_PATH'), beQuiet=False, seeUser=True, timeout=cf.g('CAMERA_PICT_SEC')*2):
        return self.TakePicture(fname, beQuiet, seeUser, timeout)

    def TakePicture(self, fname=cf.g('PICT_PATH'), beQuiet=False, seeUser=False, timeout=cf.g('CAMERA_PICT_SEC')):
        self.CheckCameraThread()
        self.be_quiet = beQuiet
        if is_dir(fname):
            filename = fname+'p'+datetime.now().strftime(cf.g('SFT_FORMAT')) +'.jpg'
        else:
            filename = fname
        if seeUser: self.take_portrait = filename
        else: self.take_picture = filename

        # wait for the picture to appear
        start_dt = datetime.now()
        target_time = datetime.now() + timedelta(seconds=timeout)
        while (not os.path.isfile(filename)) and (datetime.now() < target_time): sleep(0.25)
        if os.path.isfile(filename): return filename
        else:
            LogError(f"TakePicture timed out after {timeout} seconds.")
            return False

    def _take_picture(self, image, filename, beQuiet=False, seeUser=False):
        try:
            if isinstance(image, bool): self.cam.capture_file(filename)
            else:
                cv2.imwrite(f"{cf.g('TEMP_PATH')}temp.jpg", image)
                os.rename(f"{cf.g('TEMP_PATH')}temp.jpg", filename)
            # show the image for 3 secs and play a shutter sound
            LogInfo(f"_take_picture: seeUser={seeUser}, http://{GetIP()}/{filename}".replace('./', 'LilL3x/'))
            if not beQuiet:
                self.shutter.play()
                if self.show_view:           # freeze the camera to show pict
                    self._whatISee(image)    # show_view is set outside the loop
                    while self.show_view: sleep(0.25)
            if seeUser: self.take_portrait = False
            else: self.take_picture = False
            return filename
        except Exception as e:
            LogError(f"_take_picture: Couldn't take pict '{filename}': {e.args}")
            return False

    def SendPicture(self):
        path = self.TakePicture()
        if path:
            return self.UploadPicture(path)
        else: return False

    def UploadPicture(self, pict_path):
        url = False
        if pict_path and os.path.isfile(pict_path):

            try:
                 im = pyimgur.Imgur(cf.g('IMGUR_ID'))
                 LogDebug(f"Uploading Picture: {pict_path}")
                 uploaded_image = im.upload_image(pict_path, title="From LilL3x Uploaded with PyImgur")
                 url = uploaded_image.link
                 LogDebug(f"Uploaded URL: {url}")
            except Exception as e:
                LogError(f"Exception uploading image {e.args}")
        else: LogWarn(f"UploadPict given bad path: {pict_path}: isfile={os.path.isfile(pict_path)}")
        return url

    def SharePicture(self, beQuiet=False):
        fname = self.TakePicture(beQuiet=beQuiet)
        url = self.UploadPicture(fname)
        print(f"fname:{fname}")
        print(f"url:{url}")
        return url

    def GetEmotion(self):
        ret = self.mood
        self.mood = ""
        return ret

    def _get_emotion_thread(self, image=False, filename=cf.g('TEMP_PATH')+'mood.jpg'):
        LogDebug(f"Camera: _get_emotion_thread called at {datetime.now().strftime('%H:%M')}")
        self.mood = ""
        if isinstance(image, bool): imagePath = self.TakePicture(filename, beQuiet=True)
        else: cv2.imwrite(filename, image)
        try:
            objs = False # DeepFace.analyze(img_path=filename,  actions = ['emotion'])
            if objs: self.mood = objs[0]['dominant_emotion']
        except:
            pass
        LogDebug(f"Camera: _get_emotion_thread returned {self.mood}")
        LogDebug(f"File =  http://{GetIP()}/{filename.replace('./', 'LilL3x/')}")
        if self.mood=="neutral": self.mood=""

        SleepOn(cf.g('INTERACT_MIN')*60, STATE.ShouldQuit, 5, watchState=False, wakeOn=True)   # don't call more then every INTERACT_MIN minutes

        try: os.remove(filename)  # leave the file so it can be seen in logdebug
        except: pass
        self.mood = ""    # assume that whatever they were feeling is past after INTERACT_MIN minutes
    
    def WhoAmI(self):
        user_img = self.TakePicture(seeUser=True, beQuiet=True)
        if user_img:
           try:
               dfs = False # DeepFace.find(img_path=user_img, db_path="people/")
               LogDebug(str(dfs))
           except: 
               pass
        return
    
    def Close(self):
        self.should_quit = True
        return

def is_dir(path):
    return path[-1] == '/'

def RemoveFile(file):
    try: os.remove(file)
    except: pass

CleanDirs("./picts", r"\.jpg$")

if __name__ == '__main__':
    import face
    global STATE
    def dummy():
        pass

    pygame.mixer.init()

    face = face.Face() 
    face.SetViewControl(dummy, dummy)
    face.looking()

    STATE.ChangeState('Idle')
    c = Camera()
#    exit(0)
    try: 
        c.ShowView()
        while not c.CanISeeYou(): sleep(0.25)
        print("user seen")
        try:
            while True: sleep(10)
        except KeyboardInterrupt:
            pass

        print(c.SharePicture())

        STATE.ChangeState('Quit')
        sleep(2)
        c.Close()
        face.Close()
        sleep(2)
    except Exception as e:
        print(f"exception {e.args}")
        exit(0)
