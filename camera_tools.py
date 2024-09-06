from picamera2 import Picamera2
from picamera2.outputs import FileOutput
import cv2
import requests
import base64
from gpiozero import CPUTemperature
#import pyimgur
#import flickrapi
#import webbrowser

from time import sleep
from datetime import datetime
from  error_handling import RaiseError
import os
import shutil
from datetime import datetime, timedelta
import numpy
import time
from globals import STATE
from config import cf
import re

class Camera:

    cam = None

    def __init__(self):
        RaiseError("Camera() called")
        Picamera2.set_logging(Picamera2.ERROR)
        try:
            self.cam = Picamera2()
            video_config = self.cam.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"},
                                                 lores={"size": (320,240), "format": "YUV420"})
            self.cam.configure(video_config)
        except Exception as e:
            RaiseError(f"Unable to init Picamera: {str(e)}")
            self.cam = False
        return
       
    def GetCamera(self):
        if self.cam:
            if CPUTemperature().temperature < cf.g('CPU_MAX_TEMP'):
                self.cam.start()
                return self.cam
            else:
                return RaiseError(f"Camera not used: CPU too hot ({CPUTemperature().temperature})")
        else:
            return False
        
    def ReadCamera(self):
        if self.cam:
            try:
                return self.cam.capture_buffer("lores")
            except Exception as e:
                return RaiseError(f"Error reading camera ({str(e)})")
        return None
    
    def CloseCamera(self):
        self.cam.stop()
        return
        
    def IsDark(self, secs=cf.g('DARK_SECS_TO_DEFAULT')):
        end = datetime.now() + timedelta(seconds=secs)
        self.cam = self.GetCamera()
        if not self.cam:
            return RaiseError(f"IsDark: not able to get camera")

        means = []
        while end > datetime.now() and (not STATE.IsInteractive()):
            try:
                img = self.ReadCamera()
                means.append(numpy.mean(img) * 100 / 255)
            except Exception as e:
                RaiseError(f"Error IsDark: {str(e)}") 
        self.CloseCamera()
        if len(means)>0:
            return numpy.mean(means) <= cf.g('IS_DARK_THRESH')
        else:
            return False
    def CanISeeYou(self, secs=cf.g('LOOK_SECS_TO_DEFAULT'), pictPath=""):
        try:
            self.cam = self.GetCamera()
            if self.cam:
#                ret= (self._detect_motion(secs) or self._look_for_user(secs))
                ret =  self._look_for_user(secs, pictPath)
                self.CloseCamera()
                return ret
            return RaiseError(f"CanISeeYou: No Camera object returned!")
        except Exception as e:
            return RaiseError("CanISeeYou error: "+str(e))
    # Note: _look_for_user assumes OPEN cameara instance.
    #https://github.com/raspberrypi/picamera2/blob/main/examples/capture_motion.py
    def IsUserMoving(self, secs=cf.g('LOOK_SECS_TO_DEFAULT')):
        try:
            self.cam = self.GetCamera()
            if self.cam:
                ret= (self._detect_motion(secs))
                self.CloseCamera()
                return ret
            else:
                return RaiseError("IsUserMoving: error getting cam")
            return None
        except Exception as e:
            RaiseError("IsUserMoving: unable to get camera "+str(e))

        return _detect_motion(self, secs)

    def _detect_motion(self, secs=cf.g('LOOK_SECS_TO_DEFAULT')):
        global STATE
        prev = None
        icu = 0
        end = datetime.now() + timedelta(seconds=secs)
        while end > datetime.now() and (not STATE.ShouldWake()) and icu < cf.g('MOTDET_THRESH'):
            cur = self.ReadCamera()
            if prev is not None:
                mse = numpy.square(numpy.subtract(cur, prev)).mean()
                if mse > cf.g('MOTDET_SENS'):
                    icu = icu+1
            prev = cur
        return icu>=cf.g('MOTDET_THRESH')

    #https://github.com/raspberrypi/picamera2/blob/main/examples/opencv_face_detect.py
    def _look_for_user(self, secs=cf.g('LOOK_SECS_TO_DEFAULT'), pictPath=""):
        global STATE
        # see https://www.geeksforgeeks.org/opencv-python-program-face-detection/
        haarFolder = './haarcascades/'

        # https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml 
        face_cascade = cv2.CascadeClassifier(haarFolder + 'haarcascade_frontalface_default.xml') 

        # https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_eye.xml 
        eye_cascade = cv2.CascadeClassifier(haarFolder + 'haarcascade_eye.xml')  
        icu = 0
        end = datetime.now() + timedelta(seconds=secs)
        
        # loop runs if capturing has been initialized. 
        while end > datetime.now() and not STATE.ShouldWake() and icu<cf.g('ICU_THRESH'):
          
            # reads frames from a camera
            try: 
                img_a = self.cam.capture_array()
            except Exception as e:
                return RaiseError(f'_look_for_user: Unable to capture Array ({str(e)})')
            # convert to gray scale of each frames 
            try:
                gray = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
            except Exception as e:
                return RaiseError("_look_for_user: error in cv2.cvtColor ("+str(e)+")")
            # Detects faces of different sizes in the input image 
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces)>0:
                icu = icu+1
                if pictPath and icu==1:
                    filename = pictPath
                    if is_dir(filename):
                        filename = pictPath+'capture_'+datetime.now().strftime(cf.g('SFT_FORMAT')) +'.jpg'
                    try:
                        self.cam.capture_file(filename)
                        print(f"Writing file '{filename}'")
                    except Exception as e:
                        RaiseError(f"_look_for_user: Error writing file '{filename}' ({str(e)})")
        return icu>=cf.g('ICU_THRESH')



    def TakePicture(self, fname=cf.g('TEMP_PATH_DEFAULT'), seeUser=False):
        path = self.TakePictures(1, fname)
        return path

    def TakePictures(self, num=4, fname=cf.g('TEMP_PATH_DEFAULT'),  dur=0.25, seeUser=False):
        filename = ""
        retVal = False
        cisu = True
        # if there is not a folder create ii
        if not os.path.exists(os.path.dirname(fname)) :
            
            try:
                os.makedirs(os.path.dirname(fname))
            except Exception as e:
                return RaiseError(f"TakePictures: Create Directory '{os.path.dirname(fname)}' failed ({str(e)})")
        #write the file
        for x in range(num):
            if is_dir(fname):
                filename = fname+'capture_'+str(x)+'_'+datetime.now().strftime(cf.g('SFT_FORMAT')) +'.jpg'
            else:
                filename = fname
            print(f"Writing file '{filename}'")
            if seeUser:
                cisu = self.CanISeeYou(cf.g('LOOK_SECS_TO_DEFAULT'), filename)
            if cisu:
                try:
                    if self.GetCamera():
                        self.cam.capture_file(filename)
                        self.CloseCamera()
                        retVal = filename
                except Exception as e:
                    RaiseError(f"TakePicutres: Error writing file '{filename}' ({str(e)})")
                    return False
        return retVal

    def UploadPicture(self, pict_path):
        if not pict_path:
            return pict_path

        # Set API endpoint and headers
        url = "https://api.imgur.com/3/image"
        headers = {"Authorization": "Client-ID " + cf.g('IMGUR_ID')}

        # Read image file and encode as base64
        with open(pict_path, "rb") as file:
            data = file.read()
            base64_data = base64.b64encode(data)

        # Upload image to Imgur and get URL
        response = requests.post(url, headers=headers, data={"image": base64_data})
        print(str(response))
        url = response.json()["data"]["link"]
        return url

    def _take_picture(self, fname):        
        if is_dir(fname):
            filename = fname+'capture_'+str(x)+'_'+datetime.now().strftime(cf.g('SFT_FORMAT')) +'.jpg'
        else:
            filename = fname
        print(f"Writing file '{filename}'")
        if self.cam:
            self.cam.capture_file(filename)
            print(f"took pict '{filename}'")
            return filename
        else:
            return False
    
    def SendPicture(self):
        return self.UploadPicture(self.TakePicture())

    def Close(self):
        return

    def SharePict():
        fname=self.TakePicture()
        print(fname)
        return fname

def is_dir(path):
    return path[-1] == '/'


if __name__ == '__main__':
    global STATE

 #   STATE.ChangeState('Idle')
#    c = Camera()

  #  file = c.SendPicture()
   # print(file)
#    img_data = requests.get(file).content
#    with open('image_name.jpg', 'wb') as handler:
#        handler.write(img_data)   
#    print("Detect Motion:" + str(c.IsUserMoving()))
   # for x in range(1, 10): 
   #     print("CanISeeYou:" + str(c.CanISeeYou(10)))
#    for x in range(1,5):
#        print("IsDark: "+str(c.IsDark()))

