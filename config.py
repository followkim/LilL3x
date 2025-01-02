#!/usr/bin/env python3
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
    configFileBK = "./config/config.default"
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

        # variables that would cause a hardware change
        currAI = self.config.get('AI_ENGINE','')
#        currListen = self.config.get('LISTEN_ENGINE','')
        currSpeech = self.config.get('SPEECH_ENGINE','')
#        currWWe = self.config.get('WAKE_WORD_ENGINE','')
        currWW = self.config.get('AINAMEP','')

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

        os.system(f"touch {self.configFile}")
        self.lastLoad = datetime.now()
        SetErrorLevel(self.g('DEBUG'))  # need to set ErrorLevel manually as error_handling doesn't know about config to avoid circular

        # check for hardware uupdates
        cmds = []
        if len(currAI)>0 and currAI != self.g('AI_ENGINE'):			cmds.append(f"self.SwitchAI('{self.g('AI_ENGINE')}')")
        if len(currSpeech)>0 and currSpeech != self.g('SPEECH_ENGINE'):		cmds.append(f"self.mouth.SwitchEngine('{cf.g('SPEECH_ENGINE')}')")
        if len(currWW)>0 and currWW != self.g('WAKE_WORD'):			cmds.append(f"self.ww.SetWakeWord('{cf.g('WAKE_WORD')}')")
#        if len(currListen) >0 and currListen != self.g('LISTEN_ENGINE'):	cmds.append(f"self.ears.SwitchEngine({cf.g('LISTEN_ENGINE')})")
#        if len(currWWe)>0 and currWWe != self.config.get('WAKE_WORD_ENGINE'):	cmds.append(f"self.ChangeWW({cf.g('WAKE_WORD_ENGINE')})") TODO

        if len(cmds)>0:
            STATE.ChangeState('EvalCode')
            STATE.data = cmds
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
        update_files = -1
        try:
            repo = git.Repo(f"{os.getenv('HOME')}/LilL3x/")
            diff = self.CheckGit(repo)              #will print log messages
            update_files = len(diff)
            if update_files>0:
                LogInfo(f"Local branch {repo.active_branch.name} out of date by {update_files} file(s).")

                # first see if we can pull the files
                try: 
                    orgin = repo.remote(name='origin')
                    orgin.pull()
                except Exception as e: LogError(f"Error pulling from Git: {str(e)}")
                chk = self.CheckGit(repo) # see if we were successful
                chk_files = len(chk)
                update_files = update_files - chk_files
                LogInfo(f"Updated {update_files} files.") ## double check the pull
                if chk_files: LogWarn(f"Unable to update {chk_files} file(s).") ## TODO: determine which files

                for file in diff:
                    file_updated = not file in chk
                    LogDebug(f"\t{file.change_type}: {file.a_path} updated={file_updated}")
                    if file.a_path[-3:] == ".py" and file_updated: STATE.ChangeState('Restart') 
                    if file.a_path[-4:] == ".ppm" and file_updated:
                        STATE.ChangeState('EvalCode')  # note that this will fail if we need to restart, which is fine
                        STATE.data = ["self.face.screen.LoadFrames()"]
            else: LogInfo(f"Local branch {repo.active_branch.name} up-do-date.")
        except Exception as e: LogError(f"Error Updating Git: {str(e)}")
        return update_files

    def CheckGit(self, repo):
        try:
            repo.remotes.origin.fetch()
            remote_head = repo.remotes.origin.refs[repo.active_branch.name].commit
            local_head = repo.head.commit
            diff = local_head.diff(remote_head)
            return diff
        except Exception as e: LogError(f"Error pulling from Git: {str(e)}")
        return False

    def g(self, key, default=False):
        try:
            return self.config[key]
        except Exception as e:  #KeyError:
            LogWarn(f"Config.g: {key} not found, checking defaults...")
            if not self.LoadDefault(key):
                LogError(f"Config.g: {key} not found in defaults!")
                return default
            else: return self.config[key]

    def c(self, key, alt):
        tryK = self.g(key)
        if not tryK:
            return self.g(alt)
        else:
            return tryK

    def s(self, key, val):
        try:
            if re.search(r"^(int|num|float)", self.config_desc[key]) and isinstance(val, str):
                if val[0]=="-":  val = w2n.word_to_num(val[1:]) * -1 # w2n can't do negative numbers for some reason
                else: val = w2n.word_to_num(val)                     # convert string from int
            LogInfo(f"Config.s: Setting {key} to {val}.")
            self.config[key] = val
            self.WriteConfig()  # save whenever dirty
            if key=='DEBUG': SetErrorLevel(cf.g('DEBUG')) # error_handling doesn't have a Config object
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
    
    if len(sys.argv)>1: 
        SetErrorLevel(1)
        if len(sys.argv)==2:
            print(cf.g(sys.argv[1]))
        elif sys.argv[1].lower()[0] == "g":
            print(cf.g(sys.argv[2]))
        elif sys.argv[1].lower()[0] == "s" and len(sys.argv)==4:
            cf.s(sys.argv[2], sys.argv[3])
            print(cf.g(sys.argv[2]))
        elif sys.argv[1].lower()[0] == "c" and len(sys.argv)==4:
            print(cf.c(sys.argv[2], sys.argv[3]))

#    print(f"IsGitDirty:{bool(cf.IsGitDirty())}")

#    from time import sleep
#    print(f'LoadConfig returned {cf.LoadConfig()}')
#    print(f"IsConfigDirty={bool(cf.IsGitDirty())}")
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

