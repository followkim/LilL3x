#!/bin/bash
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
source $HOME/.bash_profile

date

cd $HOME/LilL3x

echo "running stats..."
$HOME/LilL3x/bin/python stats.py

echo "git pull..."
git pull >> ./log/git_$(date +"%Y-%m-%d").txt

echo "Run update.sh..."
. $HOME/LilL3x/install/update.sh >> ./log/update_$(date +"%Y-%m-%d").txt

echo "set alsactl..."
/usr/sbin/alsactl --file config/alsasound.state restore

echo "Starting LilL3x..."
$HOME/LilL3x/bin/python lillex.py >> ./log/launch_$(date +"%Y-%m-%d").txt 2>&1

echo "Done."
