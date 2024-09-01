import os
import sys
import inspect
from pathlib import Path
from datetime import datetime, timedelta
import re
import openai
from AI_class import AI
import requests
import json
# import parent modules
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config import cf



# import parent modules - set to parent folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE
from config import cf

class AI_Kindriod(AI):

    bearer_token = ''
    has_auth = False
    name = "Kindriod"

    def __init__(self):
        AI.__init__(self)
        self.Auth()
        print("AI Kindriod Loaded") 
        return

    def Auth(self):
        self.auth = False
        if self.AuthRefresh():
            self.has_auth = True
        return self.auth

    def AuthRefresh(self):
        need_refresh = False

        Oob = cf.g('KINDRIOD_OOB')
        refresh_token = cf.g('KINDRIOD_REFRESH_TOKEN')

        if not self.AuthBearer():

            # if the user didn't giuve the Oob, get a new one
            if Oob == 0:
                need_refresh=True
                email_url = 'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key='+cf.g('FIREBASE_WEB_API_KEY')
                email_headers = {'accept': '*/*', 'content-type': 'application/json', 'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36'}
                email_data = {
                    'requestType': 'EMAIL_SIGNIN',
                    'email': cf.g('USEREMAIL'),
                    'clientType': 'CLIENT_TYPE_WEB', 'continueUrl': 'https://kindroid.ai/', 'canHandleCodeInApp': True}
                email_responce = requests.post(email_url, headers=email_headers, data=json.dumps(email_data))
                if email_responce.status_code == 400:
                    print(f"OOb Code Request Failed: {email_responce.json()}")
                    return False

                print("Please give me the OobCode: ", end="")
                Oob=input()
            else:
                print(f"Using Oob codee {Oob}")
            if not need_refresh:
                refresh_token = cf.g('KINDRIOD_REFRESH_TOKEN')

            #Next, get the refresh Token if it's blank or we have a new oob
            if refresh_token == 0 or need_refresh:

                refresh_url = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithEmailLink?key='+cf.g('FIREBASE_WEB_API_KEY')
                refresh_headers ={ 'accept': '*/*',  'content-type': 'application/json', 'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36' }
                refresh_data = {
                    'email': cf.g('USEREMAIL'),     # Replace with the actual email
                    'oobCode': Oob      # Replace with the actual oobCode
                }
                refresh_response = requests.post(refresh_url, headers=refresh_headers, data=json.dumps(refresh_data))
                if refresh_response.status_code == 400:
                    print(f"Get Refresh failed: {refresh_responce.json()}")
                    cf.s('KINDRIOD_REFRESH_TOKEN', '')
                    cf.s('KINDRIOD_OOB', '')  # OOB used up
                    return False
                refresh_token = refresh_response.json().get("refreshToken")
                print(f"Refresh Token: {refresh_token}")
                self.AuthBearer()
        cf.s('KINDRIOD_OOB', Oob)
        cf.s('KINDRIOD_REFRESH_TOKEN', refresh_token)
        cf.WriteConfig()
        return True

    def AuthBearer(self):

        # if we don't ahve a refresh token then we shouldn't try to run
        refresh_token = cf.g('KINDRIOD_REFRESH_TOKEN')
        if refresh_token == 0:
            return False

        ## Get Bearer Token:
        bearer_url = 'https://securetoken.googleapis.com/v1/token?key='+cf.g('FIREBASE_WEB_API_KEY')
        bearer_headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://kindroid.ai',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
            'x-client-version': 'Chrome/JsCore/10.12.4/FirebaseCore-web',
            'x-firebase-gmpid': cf.g('KINDRIOD_GMPID')
        }
        bearer_data = {
            'grant_type': 'refresh_token',
            'refresh_token': cf.g('KINDRIOD_REFRESH_TOKEN')
        }

        bearer_responce = requests.post(bearer_url, headers=bearer_headers, data=bearer_data)
        if bearer_responce.status_code == 400:
            print(f"Bearer Token failed: {bearer_responce.json()}")
            return False
        self.bearer_token=bearer_responce.json().get("access_token")
        print("Bearer Token retrieved successfully")
        return True

    def respond(self, user_input, canParaphrase=True):
        img_url = None
        img_desc = None
        class_resp = AI.respond(self, user_input)  # will return either a response
#       The parent class handled the input.
        if class_resp:
            if class_resp == "Goodbye":
                user_input =  "I have to go now, goodbye"
            if user_input[0] == '#':  # its a picture
                user_input = user_input[1]
            if user_input[0] == '!':  # its an instruction
                user_input = user_input[1:]
            if user_input[0] == '@':  # its a link
                user_input = user_input[1:]
            else:
                return class_resp  # everythign else just read as is

        chat_url = 'https://api.kindroid.ai/v1/send-message'
        chat_headers = {
            'accept': 'application/json, text/plain, */*',
            'authorization': 'Bearer '+self.bearer_token,
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36'
        }
        chat_data = {
            'ai_id': cf.g('KINDRIOD_API'),
            'message': user_input,
            'stream': False, 'image_url': img_url,'image_description':img_desc,
            'internet_response': None,'link_url': None,'link_description': None
        }

        self.leds.thinking()

        # do we have a bearer token?  If not, refresh it
        if self.bearer_token == '' and not self.AuthBearer():
            self.Auth()   # full auth: set bearer and try responce again
            chat_headers['authorization'] = 'Bearer '+self.bearer_token

        # send the request
        self.leds.thinking()
        responce = requests.post(chat_url, headers=chat_headers, data=json.dumps(chat_data))
        if responce.status_code == 200:
            reply = responce.text

        # otherise, there was an error
        else:
            if not self.AuthBearer():
                self.Auth()   # full auth: set bearer and try responce again
                chat_headers['authorization'] = 'Bearer '+self.bearer_token
                responce = requests.post(chat_url, headers=chat_headers, data=json.dumps(chat_data))
                if responce.status_code != 200:  # Unable to auth
                    reply = "Sorry, I can't seem to reach the internet"
                else:
                    reply=responce.text
        reply = str(responce.text.encode('ascii', 'ignore').decode("utf-8"))
        self.leds.off()
        return reply

    #ON Startup
    def Hello(self):
        if cf.g('LAST_INTERACTION') > datetime(2024, 8, 8):
             return f"Hello {cf.g('AINAMEP')}"
        else:
             return f"Its good to meet you {cf.g('AINAMEP')}"

    def WakeMessage(self):
        resp = f"Hey {cf.g('AINAME')}"
        return self.respond(resp)
        
    
    # From Sleep State return greeting
    def Greet(self):
          resp = "Hello"
#         resp = cf.g('USERNAMEP')+" just returned after "+AI.PrettyDuration(self, datetime.now() - self.last_interaction) +", greet them."

 #       resp = AI.Greet(self)
             # and you haven't seen the user for  " + AI.PrettyDuration(datetime.now() - self.last_interaction) + ".  Greet them."
          return self.respond(resp)
    
    def Think(self):
        return AI.Think(self)

    def ObserveUser(self):
        print("looking at user")
        path = eyes.TakePicture()
        url = eyes.UploadPicture(path)
        self.respond("@" + url)
        
    def InitiateConvo(self):
        print("initialte convo")
        ret = self.ProcessMessages()
        if not ret:
            ret = f"Hey there"
#        return ret
        return self.respond(ret)

    # called from init convo -- do not process (InitCOnvo will process)
    def ProcessMessages(self):
       ret = ""
       for m in  self.messages.GetMessages():
            message = m[1]
#            ret = responces_past[m[0]] % message
       return ret


    def Close(self):
       AI.Close(self)

 
       return


if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')

    class LEDS:
        def __init__(self):
             return
        def thinking(self):
             return
        def talking(self):
             return
        def off(self):
             return
     
    ai = AI_Kindriod()
    ai.leds = LEDS()
#    ai.Greet()
#    ai.WakeMessage()
#    ai.Interact()    
#    dtd = timedelta(seconds=65)
#    ai.PrettyDuration(dtd)
    user_imp  = "hello"
    while user_imp != "quit":
        print("User: ", end="")
        user_inp = input()
        out = ai.respond(user_inp)
        print(f'AI: {out}')
