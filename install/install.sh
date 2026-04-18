sudo apt-get update

git clone -b v2 http://github.com/followkim/LilL3x/
python -m venv --system-site-packages LilL3x
  ## TODO: take action if this line isn't there
source LilL3x/bin/activate
echo "source LilL3x/bin/activate" | sudo tee -a ~/.bashrc
echo "cd ~/LilL3x/" | sudo tee -a ~/.bashrc

echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers

cd ~/LilL3x/

sudo apt-get update

sudo apt install -y python3-picamera2
sudo apt-get install -y python3-pil
sudo apt-get install -y flac
sudo apt-get install -y libportaudio2
sudo apt install -y portaudio19-dev
sudo apt-get install -y espeak
sudo apt install -y python3-libcamera python3-kms++ libcap-dev

pip install opencv-contrib-python
pip install pygame
pip install pyttsx3
pip install openai
pip install openai-whisper
pip install gtts
pip install vosk
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

pip install picamera2
pip install deepface
pip install tf-keras

##pip install libcamera

pip install llamaapi
pip install ollama
pip install langchain_ollama
pip install google.generativeai
pip install google-cloud-texttospeech
pip install anthropic
pip install PyCharacterAI
pip install characterai

#Speech regognition
pip install git+https://github.com/followkim/speech_recognition.git

# seeed voicecard
cd ~
uname -rn  # get the kernal version, should be 6.6
git clone -b v6.12 https://github.com/HinTak/seeed-voicecard/
cd seeed-voicecard/
sudo ./install.sh
sudo raspi-config #TODO automate: pick sound card, turn on i2c 
# test 
arecord -D "plughw:3,0" -f S16_LE -r 16000 -d 2 -t wav test.wav;aplay -D "plughw:3,0" test.wav

# screen
# GPIO pins: SDA: 3, SCL 5
cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
pip install adafruit-circuitpython-ssd1306

# system changes
(crontab -l; echo "@reboot sh /home/$USER/LilL3x/launch.sh >> /home/$USER/LilL3x/log/cronlog") | crontab -

#echo "Enter a password (8 letters): "
#read password

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



sudo cp ~/LilL3x/install/rclocal /etc/rc.local # if no rc.local
#sudo sed -i "s/PASSWORD/$password/g" /etc/rc.local
sudo chown root:root /etc/rc.local
sudo chmod +x /etc/rc.local

cp /etc/skel/.bashrc ~/.bashrc
cat install/bashrc >> ~/.bashrc
chmod +x ~/.bashrc
sudo chmod +x /etc/rc.local

# install website -- TODO set base folder
sudo apt-get install -y apache2
sudo apt-get install -y php
sudo rm /var/www/html/*
sudo ln ~/LilL3x/config/html/* /var/www/html/
cp ~/LilL3x/config/config.default ~/LilL3x/config/config.txt

sudo usermod -a -G www-data $USER
sudo usermod -a -G www-data www-data

sudo chmod a+x /var/www/html/*.sh
sudo chown root:root /var/www/html/*.sh
sudo chown $USER:www-data ~/LilL3x/config ~/LilL3x/config/config.txt
sudo chmod ug+rw  ~/LilL3x/config ~/LilL3x/config/config.txt
echo "%www-data ALL=NOPASSWD: /var/www/html/listwifi.sh" | sudo tee -a /etc/sudoers
echo "%www-data ALL=NOPASSWD: /var/www/html/setwifi.sh" | sudo tee -a /etc/sudoers
 #use dedicated sudoers.d file
echo "%www-data ALL=NOPASSWD: /home/$USER/LilL3x/config/html/listwifi.sh" | sudo tee /etc/sudoers.d/lill3x
echo "%www-data ALL=NOPASSWD: /home/$USER/LilL3x/config/html/setwifi.sh" | sudo tee -a /etc/sudoers.d/lill3x

#sudo rm /etc/apache2/sites-available/000-default.conf
sudo cp -l ~/LilL3x/install/apache_default.conf /etc/apache2/sites-available/lill3x.conf
sudo chown root:root /etc/apache2/sites-available/lill3x.conf
sudo chmod a+rwx /etc/apache2/sites-available/lill3x.conf
sed "s/USER/$USER/g" /etc/apache2/sites-available/lill3x.conf
sudo a2ensite lill3x.conf
sudo chmod a+rx ~
sudo systemctl restart apache2

# get default wakewords -- #TODO: just grab directory not entire repo!!
cd ~
git clone http://github.com/Picovoice/porcupine.git
cp porcupine/resources/keyword_files/raspberry-pi/* ~/LilL3x/wake
rm -rf porcupine

cd ~/LilL3x/

cd vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

cd ~/LilL3x/
