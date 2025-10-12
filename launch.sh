
#!/bin/bash
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
source $HOME/.bash_profile

date

cd $HOME/LilL3x
sudo python face.py &

echo "git pull..."
git pull >> ./log/git_$(date +"%Y-%m-%d").txt

echo "Run update.sh..."
. $HOME/LilL3x/install/update.sh >> ./log/update_$(date +"%Y-%m-%d").txt

echo preload mic
/home/el3ktra/LilL3x/bin/python mic.py

#echo "set alsactl..."
sudo /usr/sbin/alsactl --file config/alsasound.state restore

echo "Starting LilL3x..."
#mpg123 media/startup.mp3
sudo rm ".running"
sleep 1
sudo /home/el3ktra/LilL3x/bin/python lillex.py >> ./log/launch_$(date +"%Y-%m-%d").txt 2>&1

echo "Done."
