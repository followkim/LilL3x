from datetime import datetime 
import os
import re
import sys
from word2number import w2n
from error_handling import *
from globals import STATE
from time import sleep
import git 

def to_str(val=0):
    if type(val) == str: return val
    else: return str(val)

def to_int(val=0):
    return int(val)

def to_dt(val):
    # 2024-08-01 
    return datetime.strptime(val, "%Y-%m-%d")

type_f = {
    'num' : float,
    'int' : to_int,
    'str' : to_str,
    'path' : to_str,
    'key' : to_str,
    'blob' :to_str,
    'regex' :to_str,
    'dt' : to_dt
}


class Config:
    configFileBK = "./config/config.txt.default"
    configFile = "./config/config.txt"

    config= {}
    config_desc = {}
    lastLoad =  datetime.now()
    lastGit =  datetime.now()
    should_quit = False

    def __init__(self):
        self.LoadConfig()
        return

    def LoadConfig(self):
        # variables that would cause a restart
        currAI = self.config.get('AI_ENGINE','')
        currentListen = self.config.get('LISTEN_ENGINE','')
        currentSpeech = self.config.get('SPEECH_ENGINE','')
        
        # if there isn't a config file, create one from the default
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
                            LogWarn(f'Error inserting {key}:{val}: {str(e)}')

        self.lastLoad = datetime.now()
#        if currAI != self.config['AI_ENGINE'] or currentListen != self.config['LISTEN_ENGINE'] or currentSpeech != self.config['SPEECH_ENGINE']:
#            # need to change the engines here
#            return False
        SetErrorLevel(self.g('DEBUG'))  # need to set ErrorLevel manually as error_handling doesn't know about config to avoid circular
        self.WriteConfig() # needed to touch file-- line below isn't working TODO
#        os.utime(self.configFile)
        return True

    # if a value isn't found in the config file (not in git) then see if it is in the (git updatable) config file.
    def LoadDefault(self, skey):
        LogDebug(f"Checking Defaults for {skey}")
        ret = False
        with open(self.configFileBK) as file:
            for line in file:
                if re.search(r"^" + re.escape(skey.upper() + '|'), line):
                    LogDebug(f"Found key {skey} in default file: {line}")
                    ret = (line.rstrip()).split('|')
                    if len(ret):
                        key = ret.pop(0)
                        val = ret.pop(0)
                        type = ret.pop(0)
                        desc = "|".join([str(i) for i in ret])
                        try:
                            self.config[key]=type_f[type](val)
                            self.config_desc[key]=type+"|"+desc
                            ret = True
                        except Exception as e:
                            LogWarn(f'Error inserting from default {key}:{val}: {str(e)}')
        return ret

    def WriteConfig(self):
        file = open(self.configFile, "wt")
        for key in self.config.keys():
            if key == 'LAST_INTERACTION':
                file.write(key + "|" + datetime.now().strftime("%Y-%m-%d") + '|' + to_str(self.config_desc[key]) + "\n")
            else:
                file.write(key + "|" + to_str(self.config[key]) + "|" + to_str(self.config_desc.get(key, 'str')) + "\n")
        file.close()
        self.lastLoad = datetime.now()  # theself.configfile is up to date
        return True

    def IsConfigDirty(self):
        f_dt = datetime.fromtimestamp(os.path.getmtime(self.configFile))
        if f_dt > self.lastLoad:
            return True
        return False

    def IsGitDirty(self):
        self.lastGit = datetime.now()
        ret = -1
        try:
            repo = git.Repo(f"{os.getenv('HOME')}/LilL3x/")
            repo.remotes.origin.fetch()
            remote_head = repo.remotes.origin.refs[repo.active_branch.name].commit
            local_head = repo.head.commit
            diff = local_head.diff(remote_head)
            ret = len(diff)
            if diff:
                LogInfo(f"Local branch out of date by {ret} files.")
                for file in diff:
                    LogDebug(f"\t{file.change_type}: {file.a_path}")
                    if file.a_path[-3:] == ".py": STATE.ChangeState('Restart')
                    if file.a_path[-4:] == ".ppm":
                        STATE.ChangeState('EvalCode')  # note that this will fail if we need to restart, which is fine
                        STATE.data = "self.face.screen.LoadFrames()"   # will need to change to a list if I can think of other things that need reloading
                orgin = repo.remote(name='origin')
                orgin.pull()
                LogInfo(f"Updated {ret} files.")
            else: LogInfo(f"Git up-to-date")
        except Exception as e: LogError(f"Error pulling from Git: {str(e)}")
        return ret

    def g(self, key, default=False):
        try:
            return self.config[key]
        except Exception as e:  #KeyError:
            LogWarn(f"Config.g: {key} not found, checking defaults...")
            if not self.LoadDefault(key):
                LogWarn(f"Config.g: {key} not found in defaults!")
                return default
            else: return self.config[key]

    def s(self, key, val):
        try:
            if re.search(r"^int", self.config_desc[key]) and isinstance(val, str):
                if val[0]=="-":  val = w2n.word_to_num(val[1:]) * -1 # w2n can't do negative numbers for some reason
                else: val = w2n.word_to_num(val)                     # convert string from int
            LogInfo(f"Setting {key} to {val}.")
            self.config[key] = val
            self.WriteConfig()  # save whenever dirty
            SetErrorLevel(cf.g('DEBUG')) # error_handling doesn't have a Config object
            return val
        except Exception as e:
            LogWarn(f"Config.s ERR: {key} not found! ({str(e)})")
            return False

    def Close(self):
        self.IsGitDirty()
        self.should_quit = True

    def config_thread(self):
        while not self.should_quit:
            if (datetime.now()-self.lastGit).total_seconds() > cf.g('CHECK_GIT')*60 and STATE.IsInactive():  # user should be idle
                self.IsGitDirty() # will update then change state to restart!!
            dirty=self.IsConfigDirty()
            if dirty:
                LogInfo("Reloading config")
                self.LoadConfig()

            # check the file every 15s, unless it's been recently edited, then watch every 1s (as user is messing around)
            if dirty or (datetime.now()-self.lastLoad).total_seconds()<60: sleep(1)
            else: sleep(10)
        LogInfo("Config thread ended.")


currentdir = f"{os.getenv('HOME')}/LilL3x/"
sys.path.insert(0, currentdir)

# we want to Load config here so that just including will load config
cf = Config()
LogInfo("Loaded Configuration.")

if __name__ == '__main__':

    if len(sys.argv) > 1:
        print(cf.g(sys.argv[1]))

    cf.IsGitDirty()

#    from time import sleep
#    print(f'LoadConfig returned {cf.LoadConfig()}')
#    print(cf.IsGitDirty())
#    print(str(cf.config))
    # testing dirty config
    #    print(str(cf.config))

#    print(str(cf.g('ENERGY_THRESH')))
#    print(str(cf.config))

#    print(f'WriteConfig returned {cf.WriteConfig()}')
#    print(str(cf.config))

#    print(f'LoadConfig returned {cf.LoadConfig()}')
#    print(str(cf.config))
#    cf.config_thread()
