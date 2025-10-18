sudo apt-get update

git clone -b chatcat http://github.com/followkim/LilL3x/
python -m venv --system-site-packages LilL3x
  ## TODO: take action if this line isn't there
source LilL3x/bin/activate
echo "source LilL3x/bin/activate" | sudo tee -a ~/.bashrc
echo "cd ~/LilL3x/" | sudo tee -a ~/.bashrc

cd ~/LilL3x/

sudo apt-get update

sudo apt-get install -y flac
sudo apt-get install -y libportaudio2
sudo apt install -y portaudio19-dev
sudo apt-get install -y espeak
sudo apt install -y python3-kms++ libcap-dev

sudo pip install pygame  --break-system-packages 
sudo pip install SpeechRecognition --break-system-packages 
sudo pip install pyttsx3 --break-system-packages 
sudo pip install openai --break-system-packages 
sudo pip install openai-whisper --break-system-packages 
sudo pip install gtts --break-system-packages 
sudo pip install vosk --break-system-packages 
sudo pip install sounddevice --break-system-packages 
sudo pip install PyAudio --break-system-packages 
sudo pip install word2number --break-system-packages 
sudo pip install trieregex --break-system-packages 
sudo pip install gpiozero --break-system-packages 
sudo pip install rpi.gpio --break-system-packages 
sudo pip install boto3   --break-system-packages   # for AWS
sudo pip install GitPython --break-system-packages 
sudo pip install llamaapi --break-system-packages 
sudo pip install ollama --break-system-packages 
sudo pip install langchain_ollama --break-system-packages 
sudo pip install google.generativeai --break-system-packages 
sudo pip install google-cloud-texttospeech --break-system-packages 
sudo pip install anthropic --break-system-packages 

#https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage
sudo pip install PyCharacterAI --break-system-packages 
sudo pip install characterai --break-system-packages 

sudo pip3 install adafruit-blinka --break-system-packages
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel  --break-system-packages
sudo python3 -m pip install --force-reinstall adafruit-blinka  --break-system-packages

#Speech regognition
ln -s /usr/local/lib/python3.11/dist-packages/speech_recognition/__init__.py sr.py
nano sr.py

# LEDS
cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
# NOTE blinka is interactive, run this line by itself!!
sudo -E env PATH=$PATH python3 raspi-blinka.py

# seeed voicecard
cd ~
uname -rn  # get the kernal version, should be 6.6
git clone -b v6.12 https://github.com/HinTak/seeed-voicecard/
cd seeed-voicecard/
sudo ./install.sh
sudo raspi-config #TODO automate: pick sound card, turn on i2c 
# test 
arecord -D "plughw:1,0" -f S16_LE -r 16000 -d 2 -t wav test.wav;aplay -D "plughw:1,0" test.wav

# system changes
(crontab -l; echo "@reboot sh /home/el3ktra/LilL3x/launch.sh >> /home/el3ktra/LilL3x/log/cronlog") | crontab -

#echo "Enter a password (8 letters): "
#read password

sudo nmcli connection add \
 type wifi \
 con-name $HOSTNAME \
 ifname wlan0 \
 autoconnect yes \
 wifi.mode ap \
 wifi.ssid $HOSTNAME \
 wifi.band b \
 wifi.channel 1 \
 ipv4.method shared \
 ipv6.method shared

sudo cp ~/LilL3x/install/rclocal /etc/rc.local # if no rc.local
##sudo sed -i "s/PASSWORD/$password/g" /etc/rc.local
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

sudo usermod -a -G www-data el3ktra
sudo usermod -a -G www-data www-data

sudo chmod a+x /var/www/html/*.sh
sudo chown root:root /var/www/html/*.sh
sudo chown el3ktra:www-data ~/LilL3x/config ~/LilL3x/config/config.txt
sudo chmod ug+rw  ~/LilL3x/config ~/LilL3x/config/config.txt

#use dedicated sudoers.d file
#echo "%www-data ALL=NOPASSWD: /var/www/html/listwifi.sh" | sudo tee -a /etc/sudoers
#echo "%www-data ALL=NOPASSWD: /var/www/html/setwifi.sh" | sudo tee -a /etc/sudoers
echo "%www-data ALL=NOPASSWD: /home/el3ktra/LilL3x/config/html/listwifi.sh" | sudo tee /etc/sudoers.d/lill3x
echo "%www-data ALL=NOPASSWD: /home/el3ktra/LilL3x/config/html/setwifi.sh" | sudo tee -a /etc/sudoers.d/lill3x

sudo rm /etc/apache2/sites-enabled/000-default.conf
sudo cp -l ~/LilL3x/install/apache_default.conf /etc/apache2/sites-enabled/000-default.conf
sudo chown root:root /etc/apache2/sites-enabled/000-default.conf
sudo chmod a+rwx /etc/apache2/sites-enabled/000-default.conf
sudo chmod a+rx /home/el3ktra
sudo systemctl restart apache2

cd ~/LilL3x/

cd vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

cd ~/LilL3x/


cp ~/LilL3x/config/config.default ~/LilL3x/config/config.txt
