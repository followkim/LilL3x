import os 
import pandas
import shutil
from camera_tools import Camera
from error_handling import RaiseError
from datetime import datetime
from time import sleep
from globals import STATE
class ProcessOpenFace:

    app_path = "/home/el3ktra/LilL3x/OpenFace/build/bin/FeatureExtraction "
    inputs_path = "/home/el3ktra/LilL3x/OpenFace/inputs/"
    outputs_path = "/home/el3ktra/LilL3x/OpenFace/processed/"

    em = {'normal' : 0, 'happy': 1, 'sad': 2, 'surprise': 3, 'discust': 4, 'fear': 5, "angry": 6}

    headers = ['frame','face_id','timestamp','confidence','success']
    facial_units_scale = ['AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU09_r', 'AU10_r', 'AU12_r', 'AU14_r', 'AU15_r', 'AU17_r', 'AU20_r', 'AU25_r', 'AU26_r']
    facial_units_bool = ['AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c', 'AU09_c', 'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c', 'AU17_c', 'AU20_c', 'AU23_c', 'AU25_c', 'AU26_c', 'AU28_c', 'AU45_c']
    facial_units = facial_units_bool + facial_units_scale
    
    camera = None
    
    def __init__(self):
        # OPenface executable info
        return
        
    def GetMoodAU(self, camera, name='mood'):
        global STATE
        mood = ""
        path = self.inputs_path + 'mood/'
        print(f'saving data to: {path}')
        ds = self.GetDataSetFromCamera(camera, self.inputs_path + 'mood/', self.facial_units_bool)
        if ds:
            mood  = self.Interpret(ds)
        shutil.rmtree(self.inputs_path + 'mood/')
        return mood

    def GetDataSetFromCSV(self, csv, template=facial_units):
        if len(template) == 0:
            template = self.facial_units
        data_set_template = self.headers + template
        try:
            data_set = pandas.read_csv(csv, usecols=template)
            return data_set
        except Exception as e:
            return RaiseError(e)


    def GetDataSetFromCamera(self, camera, folder, template="", number=4, duration=0.25):

        dest = folder
        #if no folder, create it
        if not os.path.exists(dest):
            os.makedirs(dest)
        print(f"taking {number} pictures into {dest}: {os.path.exists(dest)}")
        picts = camera.TakePictures(number, dest, duration)
        if not picts:
           print('no one seen')
           return False
        # process the files
        try:
            cmd = self.app_path + " -fdir "+folder+" -out_dir " + dest
            print(cmd)
            exit()
            retval = os.system(cmd)
        except Exception as e:
            RaiseError(e)

        if len(template) == 0:
            template = self.facial_units
        data_set_template = self.headers + template

        print(f"Procssed into {dest}: {os.path.exists(dest+'mood.csv')}")

        try:
            data_set = self.GetDataSetFromCSV(dest+"mood.csv", template)
            return data_set
        except Exception as e:
            RaiseError(e)
            return panda.DataFrame()
        
    def Interpret(self, data_set):
        
        valstar = {
            "happy":[[1, 4], [6,12], [12]],
            "sad": [[1,4],  [1,4,15], [1,4,15,17], [6,15],[1]], # [1,4,11],[11,17,1],
            "surprised":[[1, 2, 5], [1, 2, 5, 26]],
            "disgusted": [[9, 17], [10, 17], [9, 10]],
            "afraid": [[1, 2, 4], [1, 2, 4, 5, 20], [1, 2, 4, 5, 7, 20, 26], [1, 2, 4, 5], [5, 20], [20]],
            "angry": [[4, 5, 7, 10, 23, 25], [4, 5, 7, 10, 23, 26], [4,5,7,17,23], [4,5,7,23], [4,5,7]]                    
        }

        # [01, 02, 04, 05, 06, 07, 09, 10, 12, 14, 15, 17, 20, 23, 25, 26, 28, 45_']
        # https://imotions.com/blog/learning/research-fundamentals/facial-action-coding-systself.em/#self.emotions-and-action-units


        rows = len(data_set)
        tolerance = 0.8
        curr_status= []
        mood = ""
        for col in data_set.columns:
            if col[:2] == 'AU':
                thiscol = int(col[2:4])
                avg_col = (data_set[col].sum())/rows 
                if avg_col >= tolerance:
                    curr_status.append(thiscol)
        
        curr_status.sort()
        for key in valstar.keys():
            for x in valstar[key]:
#                if x == curr_status:
                check = True
                for e in x:
                    if e not in curr_status:
                        check = False
                if check:
                    mood = mood + key + ", "
        return " and".join(mood[:-2].rpsplit(",", 1))

    def ProcessFilesintoCSV(self, dest):
                
        # if there is alrady a fodler delete it
        if os.path.exists(dest):
            try:
                shutil.rmtree(dest)
            except Exception as e:
                return RaiseError(e)
        try:
            os.makedirs(inf + inp + '/')
        except Exception as e:
            return RaiseError(e)

        try:
            print(self.app_path + " -fdir "+f+" -out_dir " + dest + " >> output.txt")
            return os.systsem(self.app_path + " -fdir "+f+" -out_dir " + dest + " >> output.txt")
        except Exception as e:
            return RaiseError(e)

    def SortFilesintoCSV(self, in_emotion):

        data_set_template = self.headers + self.facial_units
        data_set = pandas.DataFrame(columns=data_set_template)

        for self.emotion in self.em.keys():
            
            cmd = self.app_path + "-fdir " + self.inputs_path + self.emotion + " -out_dir " + self.outputs_path + " >> output.txt"
            print(f'Compiling {self.emotion}: \n{cmd}')
            os.systself.em(cmd)
            
            print(f'consdering {self.emotion}...')    
            csv_file = "/home/el3ktra/OpenFace/processed/" + self.emotion + ".csv"
            if os.path.exists(csv_file):
                print(f'Processing {csv_file}...')
                this_data_set = pandas.read_csv(csv_file, usecols=data_set_template)
                this_data_set['self.emotion'] = self.emotion
                data_set = pandas.concat([data_set, this_data_set])
                print ("Done.\n" )
            else:
                print(f'could not find {csv_file}...\n')
               
        data_set.to_csv("/home/el3ktra/OpenFace/processed/" + 'all' + ".csv", index=False)
        return csv


if __name__ == '__main__':

    global STATE
    STATE.ChangeState('Idle')
    c = Camera()

    pof = ProcessOpenFace()
    pof.GetMoodAU(c)
