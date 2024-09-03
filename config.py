from datetime import datetime 
import os.path
import re
from word2number import w2n

from state import STATE

class Config:
    configFileBK = "/home/el3ktra/LilL3x/config/config.txt.default"
    configFile = "/home/el3ktra/LilL3x/config/config.txt"

    config= {}
    config_desc = {}
    lastLoad = 0 # datetime.now()

    def __init__(self):
        self.LoadConfig()
        return

    def to_str(self, val):
        if not val:
            return ""
        if type(val) == str:
            return val
        else:
            return str(val)
    def to_int(self, val):
        return int(val)

    def to_dt(self, val):
        # 2024-08-01 
        return datetime.strptime(val, "%Y-%m-%d")

    def LoadConfig(self):
        # variables that would cause a restart
        currAI = self.config.get('AIENGINE', '')
        currentListen = self.config.get('LISTEN_ENGINE', '')
        currentSpeech = self.config.get('SPEECH_ENGINE', '')
        
        type_f = {
            'int' : self.to_int,
            'str' : self.to_str,
            'path' : self.to_str,
            'dt' : self.to_dt
        }
        
        if not os.path.isfile(self.configFile) or  os.path.getsize(self.configFile) == 0:
            os.system("cp " + self.configFileBK + " " + self.configFile)

        with open(self.configFile) as file:
            for line in file:
                if re.search(r"^([A-Z])", line):
                    ret = (line.rstrip()).split('|')
                    if len(ret):
                        key = ret.pop(0)
                        val = ret.pop(0)
                        type = ret.pop(0)
                        desc = "|".join([str(i) for i in ret])
                        try:
                            self.config[key]=type_f[type](val)
                            self.config_desc[key]=type+"|"+desc
                        except Exception as e:
                            print(f'Error inserting {key}:{val}: {str(e)}')

        self.lastLoad = datetime.now()
        if currAI != self.config['GTTS_VOICE'] or currentListen != self.config['LISTEN_ENGINE'] or currentSpeech != self.config['SPEECH_ENGINE']:
            # need to change the engines here
            return False
        self.WriteConfig()
        return True

    def WriteConfig(self):
        file = open(self.configFile, "wt")
        for key in self.config.keys():
            if key == 'LAST_INTERACTION':
                file.write(key + "|" + datetime.now().strftime("%Y-%m-%d") + '|' + self.to_str(self.config_desc[key]) + "\n")
            else:
                file.write(key + "|" + self.to_str(self.config[key]) + "|" + self.to_str(self.config_desc.get(key, 'str')) + "\n")
        file.close()
        self.lastLoad = datetime.now()  # theself.configfile is up to date

    def IsConfigDirty(self):
        f_dt = datetime.fromtimestamp(os.path.getmtime(self.configFile))
        if f_dt > self.lastLoad:
            return True
        return False

    def g(self, key, default=False):
        try:
            return self.config[key]
        except Exception as e:
            print(f"Config.g ERR: {key} not found! ({str(e)})")
            return default

    def s(self, key, val):
        try:
            if re.search(r"^int", self.config_desc[key]):
                val = w2n.word_to_num(val)
            print(f"Setting {key} to {val}.")
            self.config[key] = val
            self.WriteConfig()  # save whenever dirty
            return val
        except Exception as e:
            print(f"Config.s ERR: {key} not found! ({str(e)})")
            return False



cf = Config()
print("Loaded Configuration.")
if __name__ == '__main__':
    from time import sleep
    print(f'LoadConfig returned {cf.LoadConfig()}')
    cf.config['fdafdasfdsa']='test'
    print(f'WriteConfig returned {cf.WriteConfig()}')
    print(str(cf.config))
    print(f'LoadConfig returned {cf.LoadConfig()}')
    print(str(cf.config))
