git clone -b v2 http://github.com/followkim/LilL3x/
python -m venv --system-site-packages LilL3x
nano LilL3x/pyvenv.cfg # check that --system-site-packages is true
source LilL3x/bin/activate # also add to .bashrc
cd LilL3x

sudo apt install -y python3-picamera2
sudo apt-get install python3-pil
sudo apt-get install flac
sudo apt-get install libportaudio2
sudo apt install portaudio19-dev
sudo apt install -y python3-libcamera python3-kms++ libcap-dev

pip install opencv-contrib-python
pip install pygame
pip install SpeechRecognition
pip install pyttsx3
pip install openai
pip install gtts
pip install vosk
pip install sounddevice
pip install PyAudio
pip install pvporcupine
pip install pvrecorder
pip install word2number
pip install gpiozero
pip install rpi.gpio
pip install boto3

pip install picamera2
##pip install libcamera

pip install llamaapi
pip install ollama
pip install langchain_ollama
pip install google.generativeai
pip install anthropic

# seeed voicecard
cd ~
uname -r
git clone -b v6.6 https://github.com/HinTak/seeed-voicecard/
cd seeed-voicecard/
sudo ./install.sh
# test 
arecord -D "plughw:3,0" -f S16_LE -r 16000 -d 5 -t wav test.wav
aplay -D "plughw:3,0" test.wav
pip install picovoicedemo


# screen
cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
pippyut install adafruit-circuitpython-ssd1306

# system changes
crontab -e
@reboot sh /home/el3ktra/LilL3x/launch.sh >/home/el3ktra/LilL3x/cronlog

cd ~/Lill3x
wpa_passphrase Lill3x <passprase>
# put passprhase in local nano file
sudo nano /etc/rc.local
sudo cp config/rclocal /etc/rc.local # if no rc.local
chmod +x .bashrc
sudo chmod +x /etc/rc.local
sudo raspi-config
#Audio: pick card
#turn on i2c 

sudo apt-get install apache2
sudo apt-get install php

echo "www-data ALL=NOPASSWD: /var/www/html/listwifi.sh" | sudo tee -a /etc/sudoers
echo "www-data ALL=NOPASSWD: /var/www/html/setwifi.sh" | sudo tee -a /etc/sudoers


cd /~Lill3x
sudo ln config/html/* /var/www/html/

sudo chmod a+x /var/www/html/*.sh
sudo chown root:root /var/www/html/*
sudo chown www-data:www-data config/config.txt

sudo usermod -a -G www-data $USER
sudo usermod -a -G www-data www-data

sudo rm /etc/apache2/sites-enabled/000-default.conf 
sudo cp -l config/apache_default.conf /etc/apache2/sites-enabled/000-default.conf 
sudo chown root:root /etc/apache2/sites-enabled/000-default.conf 
sudo chmod a+rwx /etc/apache2/sites-enabled/000-default.conf 
sudo chmod a+rx /home/el3ktra
sudo systemctl restart apache2

git clone http://github.com/Picovoice/porcupine.git
cp porcupine/resources/keyword_files/raspberry-pi/* ~/LilL3x/wake
rm -r porcupine

