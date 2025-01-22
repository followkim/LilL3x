#!/bin/bash
sudo apt-get install -y espeak
. bin/activate

pip install openai-whisper
pip install google-cloud-texttospeech

cp /etc/skel/.bashrc ~/.bashrc
cat install/bashrc >> ~/.bashrc
chmod +x ~/.bashrc

