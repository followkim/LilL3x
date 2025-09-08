#!/bin/bash
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
source $HOME/.bash_profile

date

cd $HOME/LilL3x

echo "git pull..."
git pull >> ./log/git_$(date +"%Y-%m-%d").txt

echo "Run update.sh..."
. $HOME/LilL3x/install/update.sh >> ./log/update_$(date +"%Y-%m-%d").txt

echo "Checking sound card..."
l=$(eval "pactl info | grep 'Default Sink' | cut -d ':' -f 2 | xargs")
while [[ -z "$l" ]]; do
  echo "No default audio card.  Waiting."
  l=$(eval "pactl info | grep 'Default Sink' | cut -d ':' -f 2 | xargs")
  sleep 5
done
echo "Default Sound Card loaded"
pactl info | grep Sink


echo "set alsactl..."
/usr/sbin/alsactl --file config/alsasound.state restore

echo preload mic
/home/el3ktra/LilL3x/bin/python mic.py

echo "Starting LilL3x..."
sudo /home/el3ktra/LilL3x/bin/python lillex.py >> ./log/launch_$(date +"%Y-%m-%d").txt

echo "Done."
