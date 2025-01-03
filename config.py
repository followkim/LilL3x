#!/usr/bin/env python3
from datetime import datetime 
import os
import re
import sys
from word2number import w2n
from error_handling import *
from globals import STATE
from time import sleep
from datetime import datetime
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
    'bool' : int,
    'regex' :to_str,
    'dt' : to_dt
}


class Config:
    configFileStatic = "./config/config.vars"
    configFileDefault = "./config/config.default"
    configFile = "./config/config.txt"

    config= {}
    lastLoad =  datetime.now()
    lastGit =  datetime.now()
    should_quit = False

    def __init__(self):
        self.LoadConfig()
        self.CheckConfig()
        return

    def LoadConfig(self):
        currAI= ''
        currSpeech = ''
        currListen = ''
        currWW = ''
        currWWe = ''
        if 'AI_ENGINE' in self.config:
            # variables that would cause a hardware change
            currAI = self.g('AI_ENGINE','')
    #        currListen = self.config.get('LISTEN_ENGINE','')
            currSpeech = self.g('SPEECH_ENGINE','')
   #        currWWe = self.config.get('WAKE_WORD_ENGINE','')
            currWW = self.g('WAKE_WORD','')

        # if there isn't a config file, create one from the default
        if not os.path.isfile(self.configFile) or  os.path.getsize(self.configFile) == 0:
            os.system("cp " + self.configFileDefault + " " + self.configFile)

        static = self.LoadConfigDict(self.configFileStatic)
        self.config = self.LoadConfigDict(self.configFile)
        self.config.update(static)
        os.system(f"touch {self.configFile}")
        self.lastLoad = datetime.now()
        LogInfo(f"Config File loaded at {self.lastLoad.strftime('%H:%M')}")
        SetErrorLevel(self.g('DEBUG'))  # need to set ErrorLevel manually as error_handling doesn't know about config to avoid circular

        # check for hardware updates.  Blanks indicate that this is first time loading dictionary
        if currAI:
            cmds = []
            if len(currAI)>0 and currAI != self.g('AI_ENGINE'):			cmds.append(f"self.SwitchAI('{self.g('AI_ENGINE')}')")
            if len(currSpeech)>0 and currSpeech != self.g('SPEECH_ENGINE'):		cmds.append(f"self.mouth.SwitchEngine('{cf.g('SPEECH_ENGINE')}')")
            if len(currWW)>0 and currWW != self.g('WAKE_WORD'):			cmds.append(f"self.ww.SetWakeWord('{cf.g('WAKE_WORD')}')")
    #        if len(currListen) >0 and currListen != self.g('LISTEN_ENGINE'):	cmds.append(f"self.ears.SwitchEngine({cf.g('LISTEN_ENGINE')})")
    #        if len(currWWe)>0 and currWWe != self.config.get('WAKE_WORD_ENGINE'):	cmds.append(f"self.ChangeWW({cf.g('WAKE_WORD_ENGINE')})") TODO
    
            if len(cmds)>0:
                print(cmds)
                STATE.ChangeState('EvalCode')
                STATE.data = cmds
        return True


    def LoadConfigDict(self, file):
        cnfg = {}
        LogInfo(f"Loading Config file {file}")
        with open(file) as file:
            for line in file:
                (key, val, type) = self.ReadConfigLine(line)
                if key:
                    try:
                        cnfg[key] = {'val': type_f[type](val), 'type':type }
                    except Exception as e:
                        LogWarn(f'Error inserting {key}:{val}({type}) ({str(e)})')
        return cnfg

    def ReadConfigLine(self, line):
        if re.search(r"^[A-Z0-9_]*\|", line):
            ret = (line.rstrip()).split('|')
            if len(ret)>=3:
                key = ret.pop(0)
                val = ret.pop(0)
                type = ret.pop(0)
                return (key, val, type)
            else:
                LogError(f"ReadConfigLine got bad string: {line}")
        return (False, False, False)
    # if a value isn't found in the config file (not in git) then see if it is in the (git updatable) config file.

    def LoadDefault(self, skey):
        LogDebug(f"Checking Defaults for {skey}")
        ret = False
        with open(self.configFileDefault) as file:
            for line in file:
                (key, val, type) = self.ReadConfigLine(line) 
                if key and key==skey:
                    LogDebug(f"Found key {key}[{type}]:{val} in default file: {line}")
                    try:
                        self.config[key] = {'val': type_f[type](val), 'type':type }
                        return True
                    except Exception as e:
                        LogWarn(f'Error inserting from default {key}:{val}: {str(e)}')
        return False

    def WriteConfig(self):
        configFile = open(self.configFile, "wt")
 
        with open(self.configFileDefault) as file:
            for line in file:
                (key, val, type) = self.ReadConfigLine(line) 
                if key:
                    if key == 'LAST_INTERACTION':
                        configFile.write(f"{key}|{datetime.now().strftime('%Y-%m-%d')}|{self.config[key]['type']}\n")
                    else:
                        configFile.write(f"{key}|{to_str(self.config[key]['val'])}|{self.config[key]['type']}\n")
        configFile.close()
        self.lastLoad = datetime.now()  # theself.configfile is up to date
        LogInfo(f"Config File written {self.lastLoad.strftime('%H:%M')}")
        return True

    def CheckConfig(self):
        diff = False
        with open(self.configFileDefault) as file:
            for line in file:
                (key, val, type) = self.ReadConfigLine(line)
                if key:
                    if not key in self.config:
                        LogWarn(f"Config: Found New Key {key}: ({type}){val}")
                        self.config[key] = {'val': type_f[type](val), 'type':type }
                        diff=True
                    elif self.config[key]['type'] != type:
                        LogWarn(f"Config Key={key}: Default Key type {type} different from config {self.config[key]['type']}")
                        self.config[key]['val'] = val
                        self.config[key]['type'] = type
                        diff=True
        if diff: self.WriteConfig()
        return diff


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
                LogInfo(f"Updated {update_files} files at at {datetime.now().strftime('%H:%M')}") ## double check the pull
                if chk_files: LogWarn(f"Unable to update {chk_files} file(s).") ## TODO: determine which files

                for file in diff:
                    file_updated = not file in chk
                    if file_updated: LogInfo(f"\t{file.change_type}: {file.a_path} updated={file_updated}")
                    else: LogError(f"File not updated{file.change_type}: {file.a_path} updated={file_updated}")
                    if file.a_path[-3:] == ".py" and file_updated: STATE.ChangeState('Restart') 
                    if file.a_path[-4:] == ".ppm" and file_updated:
                        STATE.ChangeState('EvalCode')  # note that this will fail if we need to restart, which is fine
                        STATE.data = ["self.face.screen.LoadFrames()"]
                    if re.search(r"config.default$", file.a_path) and file_updated: self.CheckDefaults()
                    if re.search(r"config.static$",  file.a_path) and file_updated: self.LoadConfig()

            else: LogInfo(f"Local branch {repo.active_branch.name} up-do-date at {datetime.now().strftime('%H:%M')}")
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
        if key in self.config:
            return self.config[key]['val']
        else:  #KeyError:
            LogWarn(f"Config.g: {key} not found, checking defaults...")
            if not self.LoadDefault(key):
                LogError(f"Config.g: {key} not found in defaults!")
                return default
            else:
                self.WriteConfig()
                return self.config[key]['val']

    def c(self, key, alt):
        tryK = self.g(key)
        if not tryK:
            return self.g(alt)
        else:
            return tryK

    def s(self, key, val):
        try:
            if re.search(r"^(int|num|float|bool)", self.config[key]['type']) and isinstance(val, str):
                if val[0]=="-":  val = w2n.word_to_num(val[1:]) * -1 # w2n can't do negative numbers for some reason
                else: val = w2n.word_to_num(val)                     # convert string from int
            LogInfo(f"Config.s: Setting {key} to {val}.")
            self.config[key]['val'] = val
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
            if self.IsConfigDirty(): self.LoadConfig()

            # check the file every 10s, unless it's been recently edited, then watch every 1s (as user is messing around)
            if (datetime.now()-self.lastLoad).total_seconds()<60: sleep(1)
            else: sleep(10)
        LogInfo("Config thread ended.")


currentdir = f"{os.getenv('HOME')}/LilL3x/"
sys.path.insert(0, currentdir)

# we want to Load config here so that just including will load config
cf = Config()

if __name__ == '__main__':
    
    if len(sys.argv)>1: 
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
#    print(str(cf.config)+"\n\n\n\n")
#    cf.WriteConfig()
#    print(f'LoadConfig returned {cf.LoadConfig()}')
#    print(str(cf.config)+"\n\n\n\n")
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

