#!/bin/bash
sudo apt-get update

git clone -b v2 https://github.com/followkim/LilL3x/
python -m venv --system-site-packages LilL3x
source LilL3x/bin/activate
echo "source LilL3x/bin/activate" | sudo tee -a ~/.bashrc
echo "cd ~/LilL3x/" | sudo tee -a ~/.bashrc

echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers

# install the website first
sudo apt-get install -y apache2
sudo apt-get install -y php
sudo rm /etc/apache2/sites-available/000-default.conf
sudo cp -l ~/LilL3x/install/apache_default.conf /etc/apache2/sites-available/lill3x.conf
sudo chown root:root /etc/apache2/sites-available/lill3x.conf
sudo chmod a+rwx /etc/apache2/sites-available/lill3x.conf
sudo sed -i "s/USER/$USER/g" /etc/apache2/sites-available/lill3x.conf
sudo a2ensite lill3x.conf
sudo chmod a+rx ~  # needed to be able to browse folders in home folder
sudo chown $USER:www-data ~/LilL3x/
sudo rm /var/www/html/*
sudo ln ~/LilL3x/config/html/* /var/www/html/

sudo chmod a+x /var/www/html/*.sh
sudo chown root:root /var/www/html/*.sh
sudo systemctl restart apache2

# make sure the website can read the configuration file
cp -n ~/LilL3x/config/config.default ~/LilL3x/config/config.txt
sudo usermod -a -G www-data $USER
sudo usermod -a -G www-data www-data
sudo chown $USER:www-data ~/LilL3x/config ~/LilL3x/config/config.txt
sudo chmod ug+rw  ~/LilL3x/config ~/LilL3x/config/config.txt


printf '\a'
echo
echo
echo
echo The configuration website is installed.  Remaining install time is approximately 30 minutes.
echo go to http://$(hostname -I | grep -o '[0-9\.]*') to configure $HOSTNAME in the meantime!
read -p "Press Enter to continue..."

sudo apt install -y python3-picamera2
sudo apt-get install -y python3-pil
sudo apt-get install -y flac
sudo apt-get install -y libportaudio2
sudo apt install -y portaudio19-dev
sudo apt-get install -y espeak
sudo apt install -y espeak-ng libespeak1
sudo apt install -y python3-libcamera python3-kms++ libcap-dev

pip install opencv-contrib-python  # need to install first to control numpy version
pip install pygame
pip install pyttsx3
pip install openai
#pip install openai-whisper  causes error, installed below
pip install gtts
pip install vosk
pip install pocketsphinx
pip install sounddevice
pip install PyAudio
pip install pvporcupine
pip install pvrecorder
pip install word2number
pip install trieregex
pip install gpiozero
pip install rpi.gpio
pip install boto3
pip install GitPython
pip install pyimgur

pip install picamera2
pip install deepface
pip install tf-keras

pip install llamaapi
pip install ollama
pip install langchain_ollama
pip install google.genai
pip install google.generativeai
pip install google-cloud-texttospeech
pip install anthropic
pip install PyCharacterAI
pip install characterai
pip install piper-tts
pip install pydub
pip install typecast-python

python3 -m piper.download_voices --data-dir $HOME/LilL3x/voices en_US-lessac-medium

#openwakeword
pip install openwakeword --no-deps
pip install onnxruntime numpy tqdm scipy requests scikit-learn
python -c "import openwakeword; openwakeword.utils.download_models()"
cd ~/LilL3x/
ln $HOME/LilL3x/lib/python3.13/site-packages/openwakeword/resources/models/*.onnx $HOME/LilL3x/wake

#reinstall opencv-contrib -- one of the above packages install opencv
pip uninstall -y opencv-python opencv-contrib-python
pip install opencv-contrib-python

#Speech regognition
pip install git+https://github.com/followkim/speech_recognition.git

#OpenAI Whisper workaround
#mkdir ~/pip_tmp
#TMPDIR=~/pip_tmp pip install openai-whisper
#rmdir ~/pip_tmp --ignore-fail-on-non-empty



# seeed voicecard
cd ~
kernal_num=$(uname -r | grep -o '[0-9]\.[0-9]*')
git clone -b v$kernal_num https://github.com/HinTak/seeed-voicecard/
cd seeed-voicecard/
sudo ./install.sh
#sudo raspi-config #TODO automate: pick sound card, turn on i2c 
# test 
#read -p "Speak to test the voice card.  Press enter when ready."
#arecord -D "plughw:3,0" -f S16_LE -r 16000 -d 2 -t wav test.wav;aplay -D "plughw:3,0" test.wav

# get default wakewords -- #TODO: just grab directory not entire repo!!
cd ~
git clone --filter=blob:none --no-checkout  https://github.com/Picovoice/porcupine.git
cd porcupine/
git sparse-checkout init --cone
git sparse-checkout set resources/keyword_files/raspberry-pi/
git checkout
cd ~
cp porcupine/resources/keyword_files/raspberry-pi/* ~/LilL3x/wake
rm -rf porcupine




cd ~/LilL3x/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip



cp /etc/skel/.bashrc ~/.bashrc
cat ~/LilL3x/install/bashrc >> ~/.bashrc
chmod +x ~/.bashrc

# Install the backup network
sudo nmcli connection add \
 type wifi \
 con-name $HOSTNAME \
 ifname wlan0 \
 autoconnect yes \
 wifi.mode ap \
 wifi.ssid $HOSTNAME \
 wifi.band a \
 wifi.channel 157 \
 ipv4.method shared \
 ipv6.method shared

#use dedicated sudoers.d file
echo "%www-data ALL=NOPASSWD: /home/$USER/LilL3x/config/html/listwifi.sh" | sudo tee /etc/sudoers.d/lill3x
echo "%www-data ALL=NOPASSWD: /home/$USER/LilL3x/config/html/setwifi.sh" | sudo tee -a /etc/sudoers.d/lill3x


sudo cp ~/LilL3x/install/rclocal /etc/rc.local # if no rc.local
sudo chown root:root /etc/rc.local
sudo chmod +x /etc/rc.local

# screen
# GPIO pins: SDA: 3, SCL 5
cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py


##
## IF YOU SAID YES WHEN YOU WERE ASKED TO REBOOT START HERE!!
##
pip install adafruit-circuitpython-ssd1306

# system changes
(crontab -l 2>/dev/null | grep "launch.sh") || (crontab -l 2>/dev/null; echo "@reboot sh /home/$USER/LilL3x/launch.sh >> /home/$USER/LilL3x/log/cronlog") | crontab -


cd ~/LilL3x/
printf '\a'
echo
echo
echo
echo Install finished.  Please remember to set your default audio device, then reboot.
echo
echo For bookworm use raspi-config
echo for trixie use wpctl.  See https://el3ktra.net/introducing-lilll3x-the-desktop-ai-sidekick/#Setting_the_audio_device
