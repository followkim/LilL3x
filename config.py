#!/usr/bin/env python3
from datetime import datetime 
import os
import re
import sys
from word2number import w2n
from error_handling import *
from globals import STATE, SleepOn
from time import sleep
from datetime import datetime, timedelta
import git
from filelock import Timeout, FileLock

def to_str(val=0):
    if type(val) == str: return val
    else: return str(val)

def to_int(val=0):
    return int(val)

def to_dt(val):
#    return datetime.strptime(val, "%Y-%m-%d")
     return val

def to_blob(val):
    return val.replace("'", '`').replace('"', '`')

type_f = {
    'num' : float,
    'int' : to_int,
    'str' : to_str,
    'path' : to_str,
    'key' : to_str,
    'blob' :to_blob,
    'bool' : int,
    'regex' :to_str,
    'dt' : to_dt
}

def will_except(tst):
    try:
        eval(tst)
        return False
    except Exception as e:
        return True

class Config:
    configFileStatic = "./config/config.vars"
    configFileDefault = "./config/config.default"
    configFile = "./config/config.txt"

    config= {}
    lastLoad =  datetime.now()
    lastGit =  datetime.now()
    should_quit = False
    block_file =  False
    config_changed = False

    def __init__(self):
        self.LoadConfig()
        return

    def LoadConfig(self):
        currAI= ''
        currSpeech = ''
        currListen = ''
        currWW = ''
        currWWe = ''
        newConfig = {}
        # variables that would cause a hardware change
        currAI = self.sg('AI_ENGINE')
#        currListen = self.config.get('LISTEN_ENGINE','')
        currSpeech = self.sg('SPEECH_ENGINE')
#        currWWe = self.config.get('WAKE_WORD_ENGINE','')
        currWW = self.sg('WAKE_WORD')



        # if there isn't a config file, create one from the default
        if not os.path.exists(self.configFile) or  os.path.getsize(self.configFile) == 0:
            LogInfo(f"No config file!  Using default.")
            os.system("cp " + self.configFileDefault + " " + self.configFile)


        user = self.CheckConfig(self.LoadConfigDict(self.configFile), self.LoadConfigDict(self.configFileDefault))  # laod first to override any leftovers in confileFile
        static = self.CheckConfig(self.LoadConfigDict(self.configFileStatic))
        if len(static)<25: LogError(f"LoadConfig: {self.configFileStatic} is blank!")
        else: newConfig = static

        if len(user)<25: LogError(f"LoadConfig: {self.configFile} is blank!")
        else: newConfig.update(user)
#        self.config.update(self.LoadConfigDict(self.configFile))

        if len(newConfig)>75:
            self.config = newConfig
            self.lastLoad = datetime.now() + timedelta(seconds=1)
            LogInfo(f"Config File loaded at {self.lastLoad.strftime('%Y-%m-%d %H:%M:%S')}")
            SetErrorLevel(self.sg('DEBUG'))  # need to set ErrorLevel manually as error_handling doesn't know about config to avoid circular
            if self.config_changed: self.WriteConfig()
        else: return False

        # check for hardware updates.  Blanks indicate that this is first time loading dictionary
        if currAI:
            cmds = []
            if currAI and currAI != self.sg('AI_ENGINE'):   	 		cmds.append(f"self.SwitchAI('{self.sg('AI_ENGINE')}')")
            if currSpeech and currSpeech != self.sg('SPEECH_ENGINE'):		cmds.append(f"self.mouth.SwitchEngine('{cf.sg('SPEECH_ENGINE')}')")
            if currWW and currWW != self.sg('WAKE_WORD'):			cmds.append(f"self.ww.SetWakeWord('{cf.sg('WAKE_WORD')}')")
    #        if len(currListen) >0 and currListen != self.g('LISTEN_ENGINE'):	cmds.append(f"self.SwitchListenEngine({cf.sg('LISTEN_ENGINE')})")
    #        if len(currWWe)>0 and currWWe != self.config.get('WAKE_WORD_ENGINE'):	cmds.append(f"self.ChangeWW({cf.sg('WAKE_WORD_ENGINE')})") TODO

            if len(cmds)>0:
                STATE.ChangeState('EvalCode')
                STATE.data = cmds
        return True

    def CheckConfig(self, load, check=False):
        if not check: iter = load
        else: iter = check

        for key in iter:
            try:
                if (check and key not in load):
                    LogWarn(f"CheckConfig: Key {key} not found, using defaults")
                    load[key] = {'val': type_f[check[key]['type']](check[key]['val']), 'type': check[key]['type'] }
                    self.config_changed = True
                if (load[key]['type']=='path' and load[key]['val']=='') or will_except("type_f['" + load[key]['type'] + "']('" + str(load[key]['val']) + "')"):
                    LogWarn(f"LoadConfig: Data Mismatch for '{key}': [" + "type_f['"+load[key]['type']+"']('"+str(load[key]['val'])+"') ]")
                    if check:
                        load[key] = {'val': type_f[check[key]['type']](check[key]['val']), 'type': chec[key]['type'] }
                        self.config_changed = True
                if check and load[key]['type'] != check[key]['type']:
                    LogWarn(f"CheckConfig Type Error for key '{key}': Config={load[key]['type']}: Default Key type {check[key]['type']}")
                    load[key]['val'] = check[key]['val']
                    load[key]['type'] = check[key]['type']
                    self.config_changed = True
            except Exception as e:
                LogError(f"CheckConfig got exception on key {key}: {str(e)}: {str(e.args)}")
        return load

    def IsConfigDirty(self):
        f_dt = datetime.fromtimestamp(max(os.path.getmtime(self.configFile), os.path.getmtime(self.configFileStatic)))
        if f_dt > self.lastLoad:
            return True
        return False

    def LoadConfigDict(self, fileName):
        cnfg = {}
        self.LockFile()
        with open(fileName) as file:
            for line in file:
                (key, val, type) = self.ReadConfigLine(line)
                if key:
                    try:
                        cnfg[key] = {'val': type_f[type](val), 'type':type }
                    except Exception as e:
                        LogWarn(f'Error inserting {key}:{val}({type}) ({e.args})')
        os.system(f"sudo touch {fileName}")
        self.UnlockFile()
        return cnfg

    def ReadConfigLine(self, line):
        try:
            # Check for speacuial "REGEX entries"
            m = re.search("^([A-Z|_]*)\|(.*)\|REGEX", line)
            if m: return (m.group(1), m.group(2), "REGEX")
            elif re.search("^[A-Z0-9_]*\|", line):
                ret = (line.rstrip()).split('|')
                if len(ret)>=3:
                    key = ret.pop(0)
                    val = ret.pop(0)
                    type = ret.pop(0)
                    return (key, val, type)
                else:
                    LogError(f"ReadConfigLine got bad string: {line}")
        except Exception as e: LogError(f"ReadConfigLine encountered an exception parsing '{line}': (str{e}))")
        return (False, False, False)

    def LockFile(self):
        while self.block_file: sleep(0.1)
        self.block_file = True

    def UnlockFile(self):
        self.block_file = False

    def WriteConfig(self):
        newConfig = ""
        tempFile = self.configFile+"bk"
        try:

            # read the default config file
            dict = self.LoadConfigDict(self.configFileDefault)
            for key in dict:
               newConfig = f"{newConfig}{key}|{to_str(self.config[key]['val'])}|{dict[key]['type']}\n"

            if len(newConfig)>0:
                newConfig = f"{newConfig}##### LilL3x Config.WriteConfig: Written at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
             
                with open(tempFile, "w") as configFileTemp:
                    configFileTemp.write(newConfig)
                    configFileTemp.close()
 
                if (os.path.getsize(tempFile) > 0):
                    self.LockFile()
                    os.rename(tempFile, self.configFile)
                    os.system(f"sudo chown www-data:www-data {self.configFile}; sudo chmod a+w {self.configFile}")
                    self.UnlockFile()
                    self.lastLoad = datetime.now()  # theself.configfile is up to date
                    LogInfo(f"Config File written {self.lastLoad.strftime('%Y-%m-%d %H:%M:%S')}")
                    self.config_changed = False
                    return True
                else: LogError(f"WriteConfig: temp file {tempFile} is empty!")
            else: LogError(f"WriteConfig: unable to read {self.configFileDefault}")
        except Exception as e:
            LogError(f"WriteConfig exception: {e.args}")
        return False

    def IsGitDirty(self):
        self.lastGit = datetime.now()
        update_files = -1
        try:
            repo = git.Repo(f"{os.getenv('HOME')}/LilL3x/")
            diff = self.CheckGit(repo)
            update_files = len(diff)
            if update_files>0:
                LogInfo(f"Local branch {repo.active_branch.name} out of date by {update_files} file(s).")

                # first see if we can pull the files
                try: 
                    orgin = repo.remote(name='origin')
                    orgin.pull()
                except Exception as e: LogError(f"Error pulling from Git: {e.args}")

                chk = self.CheckGit(repo) # see if we were successful
                chk_files = len(chk)
                update_files = update_files - chk_files
                LogInfo(f"Updated {update_files} file(s) at at {datetime.now().strftime('%H:%M')}") ## double check the pull
                if chk_files: LogWarn(f"Unable to update {chk_files} file(s).") ## TODO: determine which files

                for file in diff:
                    file_updated = not file in chk
                    if file_updated: LogInfo(f"\t[{file.change_type}]:{file.a_path}")
                    else: LogError(f"File not updated:  [{file.change_type}]:{file.a_path}")

                    if re.search(r"update.sh$",  file.a_path) and file_updated: os.system(f"sudo bash {file.a_path}")
                    if file.a_path[-3:] == ".py" and file_updated: STATE.ChangeState('Restart')
                    if file.a_path[-4:] == ".ppm" and file_updated:
                        STATE.ChangeState('EvalCode')  # note that this will fail if we need to restart, which is fine
                        STATE.data = ["self.face.screen.LoadFrames()"]
#                    if re.search(r"config.default$", file.a_path) and file_updated: self.CheckDefaults()
                    if re.search(r"config.(vars|default)$",  file.a_path) and file_updated: self.LoadConfig()

            else: LogInfo(f"Local branch {repo.active_branch.name} up-do-date at {datetime.now().strftime('%H:%M')}")
        except Exception as e: LogError(f"Error Updating Git: {e.args}")
        return update_files

    def CheckGit(self, repo):
        try:
            repo.remotes.origin.fetch()
            remote_head = repo.remotes.origin.refs[repo.active_branch.name].commit
            local_head = repo.head.commit
            diff = local_head.diff(remote_head)
            return diff
        except Exception as e: LogError(f"Error pulling from Git: {e.args}")
        return False
    
    def sg(self, key, default=False):
        '''simple get'''
        if key not in self.config: return default
        else: return self.config[key]['val']

    def g(self, key, default=False):
#        if self.IsConfigDirty(): self.LoadConfig()
        if key in self.config:
            try:
                return self.config[key]['val']
            except Exception as e: LogError(f"Config.g caught exception: {e.args}")
        else: return default

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
            if key=='DEBUG': SetErrorLevel(cf.g('DEBUG')) # error_handling doesn't have a Config object
            self.WriteConfig()  # save whenever dirty
            return val

        except Exception as e:
            LogWarn(f"Config.s ERR: {key} not found! ({e.args})")
            return False

    def Close(self):
        self.IsGitDirty()
        self.should_quit = True

    def config_thread(self):
        while not self.should_quit:
            try:
                if (datetime.now()-self.lastGit).total_seconds() > cf.g('CHECK_GIT')*60 and STATE.IsInactive():  # user should be idle
                   self.IsGitDirty() # will update then change state to restart!!
                if self.IsConfigDirty(): self.LoadConfig()

                # check the file every 10s, unless it's been recently edited, then watch every 1s (as user is messing around)
                if (datetime.now()-self.lastLoad).total_seconds()<60:  SleepOn(60, self.config_wake, 1)
                else:  SleepOn(-1, self.config_wake, 10)
            except  Exception as e:
                LogError(f"ConfigThread uncaught exception {e.args}")
        LogInfo("Config thread ended.")

    def config_wake(self):
        return ((datetime.now()-self.lastGit).total_seconds() > cf.g('CHECK_GIT')*60 and STATE.IsInactive()) or self.IsConfigDirty() or self.should_quit

# we want to Load config here so that just including will load config
cf = Config()

if __name__ == '__main__':
    SetErrorLevel(4)
    if len(sys.argv)>1: 
        if len(sys.argv)==2:
            print(cf.g(sys.argv[1].upper()))
        elif len(sys.argv)==3:
            if sys.argv[1].lower()[0] == "g": print(cf.g(sys.argv[2].upper()))
            else: print(cf.s(sys.argv[1].upper(), sys.argv[2]))
        elif len(sys.argv)==4:
            if sys.argv[1].lower()[0] == "s": cf.s(sys.argv[2].upper(), sys.argv[3])
            elif sys.argv[1].lower()[0] == "c": print(cf.c(sys.argv[2].upper(), sys.argv[3].upper()))
            
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

