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

def to_str(val=0):
    if type(val) == str: return val
    else: return str(val)

def to_int(val=0):
    return int(val)

def to_dt(val):
     return val

def to_blob(val):
    return val.replace("'", '`').replace('"', '`')

def from_regex(regex):
    ascii = ",".join(map(str, list(val.encode('ascii'))))
    return ascii

def to_regex(regex):
    ascii = regex.split(",")
    return ''.join(chr(int(num)) for num in ascii)

type_f = {
    'num' : float,
    'float' : float,
    'int' : to_int,
    'str' : to_str,
    'path' : to_str,
    'key' : to_str,
    'blob' :to_blob,
    'bool' : int,
    'regex' : to_str,
    'dt' : to_dt
}

def will_except(tst):
    try:
        eval(tst)
        return False
    except Exception as e:
        return True

class Config:
    configFileStatic = f"./config/config.vars"
    configFileDefault = f"./config/config.default"
    configFile = f"./config/config.txt"
    configFileLock = f"./config/config.txt.LOCK"

    config= {}
    configDef= {}
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

        # variables that would cause a class change
        currAI = self.g('AI_ENGINE')
        currListen = self.g('LISTEN_ENGINE')
        currSpeech = self.g('SPEECH_ENGINE')
        currWWe = self.g('WAKE_WORD_ENGINE')
        currWW = self.g('WAKE_WORD')
#        currAudioProfile = self.g('AUDIO_PROFILE') TODO
#        currFramesProfile = self.g('FRAMES_PROFILE')

        # if there isn't a config file, create one from the default
        if not os.path.exists(self.configFile) or  os.path.getsize(self.configFile) == 0:
            LogWarn(f"No config file!  Using default.")
            os.system("cp " + self.configFileDefault + " " + self.configFile)

        
        static = self.CheckConfig(self.LoadConfigDict(self.configFileStatic))
        if len(static)<25: LogError(f"LoadConfig: {self.configFileStatic} is too short! ({len(static)})")
        else: newConfig = static
        
        self.configDef = self.LoadConfigDict(self.configFileDefault, isDict=True)
        user = self.CheckConfig(self.LoadConfigDict(self.configFile), self.configDef)  # laod first to override any leftovers in confileFile
        if len(user)<25: LogError(f"LoadConfig: {self.configFile} is too short! ({len(user)})")
        else: newConfig.update(user)
#        self.config.update(self.LoadConfigDict(self.configFile))

        if len(newConfig)>75:
            self.config = newConfig
            self.lastLoad = datetime.now()
            LogInfo(f"Config File loaded at {self.lastLoad.strftime(self.g('CONFIG_DT_FORMAT'))}")
            SetErrorLevel(self.g('DEBUG'))  # need to set ErrorLevel manually as error_handling doesn't know about config to avoid circular
            if self.config_changed: self.WriteConfig()
        else:
            LogError(f"LoadConfig: {self.configFile} is too short! ({len(newConfig)})")

        # check for hardware updates.  Blanks indicate that this is first time loading dictionary
        if currAI:
            cmds = []
            if currAI and currAI != self.g('AI_ENGINE'):   	 	cmds.append(f"self.SwitchAI('{self.g('AI_ENGINE')}')")
            if currSpeech and currSpeech != self.g('SPEECH_ENGINE'):	cmds.append(f"self.mouth.SwitchEngine('{self.g('SPEECH_ENGINE')}')")
            if currWW and currWW != self.g('WAKE_WORD'):		cmds.append(f"self.ww.SetWakeWord('{self.g('WAKE_WORD')}')")
            if currListen and currListen != self.g('LISTEN_ENGINE'):	cmds.append(f"self.SwitchListener('{self.g('LISTEN_ENGINE')}')")
            if currWWe and currWWe != self.g('WAKE_WORD_ENGINE'):	cmds.append(f"self.SwitchWakeWord('{self.g('WAKE_WORD_ENGINE')}')") 

            if len(cmds)>0:
                STATE.ChangeState('EvalCode')
                STATE.data = cmds
        return len(self.config)

    def CheckConfig(self, load, check=False):
        if not check: iter = load
        else: iter = check

        for key in iter:
            try:
                reload = False
                if (check and key not in load):
                    LogWarn(f"CheckConfig: Key {key} not found, using defaults")
                    load[key] = {'val': type_f[check[key]['type']](check[key]['val']), 'type': check[key]['type'] }
                    reload = True

                if will_except("type_f['" + load[key]['type'] + "']('" + str(load[key]['val']) + "')"):
                    LogWarn(f"CheckConfig: Exception for '{key}': [" + "type_f['"+load[key]['type']+"']('"+str(load[key]['val'])+"') ]")
                    if check:
                        reload = True
                if check:
                    if load[key]['type'] != check[key]['type']:
                        LogWarn(f"CheckConfig Type Error for key '{key}': Config={load[key]['type']}: Default Key type {check[key]['type']}")
                        reload = True

                    if  (load[key]['type'] in ('path', 'dt') or check[key]['req']) and load[key]['val'] in ('', '0'):
                        LogWarn(f"CheckConfig Blank '{key}': using default {check[key]['val']}")
                        reload = True
                    if reload:
                        load[key] = {'val': type_f[check[key]['type']](check[key]['val']), 'type': check[key]['type'] }
                        self.config_changed = True

            except Exception as e:
                LogError(f"CheckConfig got exception on key {key}: {str(e)}: {str(e.args)}")
        return load

    def IsConfigDirty(self):
        try:
            f_dt = datetime.fromtimestamp(max(os.path.getmtime(self.configFile), os.path.getmtime(self.configFileStatic)))
            if f_dt > self.lastLoad:
                return True
        except Exception as e:
            LogWarn(f'IsConfigDirty Caught Exception: {e.args}')
        return False

    def LoadConfigDict(self, fileName, isDict=False):
        cnfg = {}
        self.LockFile()
        try:
            with open(fileName) as file:
                for line in file:
                    (key, val, type, req) = self.ReadConfigLine(line)
                    if key:
                        try:
                            cnfg[key] = {'val': type_f[type](val), 'type':type }
                            if isDict: cnfg[key]['req'] = req
                        except Exception as e:
                            LogWarn(f'Error inserting {key}:{val}({type}) ({e.args})')
            if not isDict: os.system(f"sudo touch {fileName}")
        except Exception as e:
            LogError(f'LoadConfigDict ({fileName}) caught exception: ({e.args})')

        self.UnlockFile()
        return cnfg

    def ReadConfigLine(self, line):
        req = False
        try:
            # Check for speacuial "REGEX entries"
            m = re.search(r"^([A-Z|_]*)\|(.*)\|regex", line)
            if m: return (m.group(1), m.group(2), "regex", False)
            elif re.search(r"^[A-Z0-9_]*\|", line):
                ret = (line.rstrip()).split('|')
                if len(ret)>=3:
                    key = ret[0]
                    val = ret[1]
                    type = ret[2]
                else:
                    LogError(f"ReadConfigLine got bad string: {line}")
                if len(ret)>=4: req=ret[3]=='1'
                return (key, val, type, req)
        except Exception as e: LogError(f"ReadConfigLine encountered an exception parsing '{line}': (str{e}))")
        return (False, False, False, False)

    def LockFile(self):
        SleepOn(varf=self.IsLocked, step=0.1, watchState=False, wakeOn=False)
        os.system(f"touch {self.configFileLock}")
        self.block_file = True

    def IsLocked(self):
        if os.path.exists(self.configFileLock):
            if (datetime.now()-datetime.fromtimestamp(os.path.getmtime(self.configFileLock))).seconds > 10:
                LogWarn(f"Config.BreakLock: lock is {(datetime.now()-datetime.fromtimestamp(os.path.getmtime(self.configFileLock))).seconds} seconds old , must break.")
                self.BreakLock()
                LogInfo("Config.BreakLock: lock broken.")
                return False
            else: return True
        else: return False

    def BreakLock(self):
        while os.path.exists(self.configFileLock):
            try:
                os.remove(self.configFileLock)
            except:
                pass

    def UnlockFile(self):
        self.BreakLock()
        self.block_file = False

    def WriteConfig(self):
        ret = False
        newConfig = ""
        tempFile = self.configFile+"bk"
        try:

            # read the default config file
            dict = self.configDef
            for key in dict:
               if dict[key]['type'] == 'blob': newConfig = f"{newConfig}{key}|{to_blob(self.config[key]['val'])}|{dict[key]['type']}\n"
               elif dict[key]['type'] == 'regex': newConfig = f"{newConfig}{key}|{re.escape(self.config[key]['val'])}|{dict[key]['type']}\n"
               else:
                   newConfig = f"{newConfig}{key}|{to_str(self.config[key]['val'])}|{dict[key]['type']}\n"

            if len(newConfig)>0:
                newConfig = f"{newConfig}##### {GetHostname()} Config.WriteConfig: Written at {datetime.now().strftime(self.g('CONFIG_DT_FORMAT'))}\n"
             
                with open(tempFile, "w") as configFileTemp:
                    configFileTemp.write(newConfig)
                    configFileTemp.close()
 
                if (os.path.getsize(tempFile) > 0):
                    self.LockFile()
                    try:
                        os.rename(tempFile, self.configFile)
                        os.system(f"sudo chown {os.getenv('USER')}:www-data {self.configFile} config ; sudo chmod ug+rw {self.configFile}; sudo chmod ug+rwx config")
                        self.lastLoad = datetime.now()  # theself.configfile is up to date
                        LogInfo(f"Config File written {self.lastLoad.strftime(self.g('CONFIG_DT_FORMAT'))}")
                        self.config_changed = False
                        ret = True
                    except Exception as e:
                        LogError(f'WriteConfig caught exception: ({e.args}) writing to {os.getcwd()}')
                    self.UnlockFile()
                else: LogError(f"WriteConfig: temp file {tempFile} is empty!")
            else: LogError(f"WriteConfig: unable to read {self.configFileDefault}")
        except Exception as e:
            LogError(f"WriteConfig exception: {e.args}")
        return ret

    def CheckGit(self):
        self.lastGit = datetime.now()
        update_files = -1
        try:
            repo = git.Repo(f"{os.getenv('HOME')}/LilL3x/")
            diff = self.GitDiff(repo)
            update_files = len(diff)
            if update_files>0:
                LogInfo(f"Local branch {repo.active_branch.name} out of date by {update_files} file(s).")

                # first see if we can pull the files
                try: 
                    orgin = repo.remote(name='origin')
                    orgin.pull()
                except Exception as e: LogError(f"Error pulling from Git: {e.args}")

                chk = self.GitDiff(repo) # see if we were successful
                chk_files = len(chk)
                update_files = update_files - chk_files
                LogInfo(f"Updated {update_files} file(s) at at {datetime.now().strftime('%H:%M')}") ## double check the pull
                if chk_files: LogWarn(f"Unable to update {chk_files} file(s).") ## TODO: determine which files

                for file in diff:
                    file_updated = not file in chk
                    if file_updated: LogInfo(f"\t[{file.change_type}]:{file.a_path}")
                    else: LogError(f"File not updated:  [{file.change_type}]:{file.a_path}")

                    if re.search(r"update.sh$",  file.a_path) and file_updated: os.system(f"bash {file.a_path} &")
                    if file.a_path[-3:] == ".py" and file_updated: STATE.ChangeState('Restart')
                    if file.a_path[-4:] == ".ppm" and file_updated:
                        STATE.ChangeState('EvalCode')  # note that this will fail if we need to restart, which is fine.  Changed will happen on restart
                        STATE.data = ["self.face.screen.LoadFrames()"]
#                    if re.search(r"config.default$", file.a_path) and file_updated: self.CheckDefaults()
#                    if re.search(r"config.(vars|default)$",  file.a_path) and file_updated: self.LoadConfig()

            else: LogInfo(f"Local branch {repo.active_branch.name} up-do-date at {datetime.now().strftime('%H:%M')}")
        except Exception as e: LogError(f"Error Updating Git: {e.args}")
        return update_files

    def GitDiff(self, repo):
        try:
            repo.remotes.origin.fetch()
            remote_head = repo.remotes.origin.refs[repo.active_branch.name].commit
            local_head = repo.head.commit
            diff = local_head.diff(remote_head)
            return diff
        except Exception as e: LogError(f"Error pulling from Git: {e.args}")
        return False

    def CheckFiles(self):
        # check if we were asked to reboot or reset
        if os.path.exists(".restart"):
            STATE.ChangeState('Restart')
            os.remove('.restart')
        if os.path.exists(".reboot"):
            STATE.ChangeState('Reboot')
            os.remove('.reboot')
        if os.path.exists(".quit"):
            STATE.ChangeState('Quit')
            os.remove('.quit')
        return STATE.ShouldQuit() 



    def g(self, key, default=False):
#        if self.IsConfigDirty(): self.LoadConfig()
        if key in self.config:
            try:
                return self.config[key]['val']
            except Exception as e: LogError(f"Config.g caught exception: {e.args}")
        else: return default

    def d(self, key):
#        if self.IsConfigDirty(): self.LoadConfig()
        if key in self.configDef:
            try:
                return self.configDef[key]['val']
            except Exception as e: LogError(f"Config.d caught exception: {e.args}")
        else: return False


    def c(self, key, alt):
        tryK = self.g(key)
        if not tryK:
            return self.g(alt)
        else:
            return tryK

    def dc(self, key): self.cd(key)
    def cd(self, key):
        tryK = self.g(key)
        if not tryK:
            return self.d(key)
        else:
            return tryK

    def w(self, key=False, val=False):
        if key: self.s(key, val)
        self.WriteConfig()

    def s(self, key, val):
        try:
            if re.search(r"^(int|bool)", self.config[key]['type']) and isinstance(val, str):
                val = int(val)
            if re.search(r"^(float|num)", self.config[key]['type']) and isinstance(val, str):
                val = float(val)

            LogDebug(f"Config.s: Setting {key} to {val}.")
            self.config[key]['val'] = val
            if key=='DEBUG': SetErrorLevel(self.g('DEBUG')) # error_handling doesn't have a Config object
            self.config_changed = True
            return val

        except Exception as e:
            LogWarn(f"Config.s ERR: {key} not found! ({e.args})")
            return False

    def Close(self):
        self.CheckGit()
        self.should_quit = True

    today = datetime.now()
    def config_thread(self):
        error = False 
        while not self.should_quit:
            self.today = datetime.now()
            try:
                if (self.today-self.lastGit).total_seconds() > self.g('CHECK_GIT')*60 and STATE.IsInactive():  # user should be idle
                    if self.config_changed: self.WriteConfig() # periodically write just in case
                    self.CheckGit() # will update then change state to restart!!
                    #UploadLog()

                if self.IsConfigDirty(): self.LoadConfig()

                # check the file every 10s, unless it's been recently edited, then watch every 1s (as user is messing around)
                if (self.today-self.lastLoad).total_seconds()<60:  SleepOn(60, self.config_wake, 1)
                else:  SleepOn(-1, self.config_wake, 10)
            except  Exception as e:
                LogError(f"ConfigThread exception {e.args}")
                if error: self.should_quit = True
                else: self.error = True                    # prevent runaway exceptions
        LogInfo("Config thread ended.")
        self.WriteConfig()

    # this is "dirty" because it will always return false in order to prevent waking a loop.  TODO fix
    def NewDay_dirty(self):
        if datetime.now().date() != self.today.date(): #new day
            CleanDirs(cf.g('TEMP_PATH'), r"^[^\.]", 12)
            CleanDirs("./log", r"\.(log|txt)$", 30*24)
            CleanDirs("./picts", r"\.jpg$")
            CloseLog("It's a New Day")
            InitLogFile()
            self.today = datetime.now()
            return False # hacky but True will wake the loop
        return False

    def config_wake(self):
        return ((datetime.now()-self.lastGit).total_seconds() > self.g('CHECK_GIT')*60 and STATE.IsInactive()) or self.IsConfigDirty() or self.NewDay_dirty() or self.CheckFiles() or self.should_quit

#
# we want to Load config here so that just including will load config
cf = Config()

if __name__ == '__main__':

    SetErrorLevel(4)
    if len(sys.argv)>1:
        if len(sys.argv)==2:
            print(cf.g(sys.argv[1].upper()))
        elif len(sys.argv)==3:
 
            if   sys.argv[1].lower()[0] == "g": print(cf.g(sys.argv[2].upper()))
            elif sys.argv[1].lower()[0] == "d": print(cf.d(sys.argv[2].upper()))
            elif sys.argv[1].lower()   == "cd": print(cf.cd(sys.argv[2].upper()))
            else: print(cf.s(sys.argv[1].upper(), sys.argv[2]))
        elif len(sys.argv)==4:
            if   sys.argv[1].lower()[0] == "s": cf.s(sys.argv[2].upper(), sys.argv[3])
            elif sys.argv[1].lower()[0] == "w": cf.w(sys.argv[2].upper(), sys.argv[3])
            elif sys.argv[1].lower()[0] == "c": print(cf.c(sys.argv[2].upper(), sys.argv[3].upper()))
    else:
        print("Starting Config Stress Test")
        try:
            while True:
                cf.LoadConfig()
                cf.WriteConfig()
        except Exception as e: 
            print(f"Exception Caught: {e.args}")
    
#    print(f"CheckGit:{bool(cf.CheckGit())}")

#    from time import sleep
#    print(str(cf.config)+"\n\n\n\n")
#    print(f'LoadConfig returned {cf.LoadConfig()}')
#    print(str(cf.config)+"\n\n\n\n")
#    print(f"IsConfigDirty={bool(cf.CheckGit())}")
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

