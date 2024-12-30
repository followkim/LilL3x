#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
source $HOME/.bash_profile

date

cd /home/el3ktra/LilL3x/

echo "running stats..."
/home/el3ktra/LilL3x/bin/python stats.py

echo "git pull..."
git pull

echo "set alsactl..."
/usr/sbin/alsactl --file config/alsasound.state restore

echo "Starting LilL3x..."
/home/el3ktra/LilL3x/bin/python lillex.py > lillog.bk.txt

echo "Done."
