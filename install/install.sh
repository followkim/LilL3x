git clone -b v2 http://github.com/followkim/LilL3x/
python -m venv --system-site-packages LilL3x
cat pyvenv.cfg | grep "include-system-site-packages = true"  ## TODO: take action if this line isn't there
source LilL3x/bin/activate
echo "source LilL3x/bin/activate" | sudo tee -a ~/.bashrc
echo "cd ~/LilL3x/" | sudo tee -a ~/.bashrc

cd ~/LilL3x/
mkdir log
mkdir temp

sudo apt install -y python3-picamera2
sudo apt-get install python3-pil
sudo apt-get install flac
sudo apt-get install libportaudio2
sudo apt install portaudio19-dev
sudo apt-get install espeak
sudo apt install -y python3-libcamera python3-kms++ libcap-dev

pip install opencv-contrib-python
pip install pygame
pip install SpeechRecognition
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
##pip install libcamera

pip install llamaapi
pip install ollama
pip install langchain_ollama
pip install google.generativeai
pip install anthropic

# seeed voicecard
cd ~
uname -rn  # get the kernal version, should be 6.6
git clone -b v6.6 https://github.com/HinTak/seeed-voicecard/
cd seeed-voicecard/
sudo ./install.sh
sudo raspi-config #TODO automate: pick sound card, turn on i2c 
# test 
arecord -D "plughw:3,0" -f S16_LE -r 16000 -d 2 -t wav test.wav;aplay -D "plughw:3,0" test.wav

# screen
cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
pippyut install adafruit-circuitpython-ssd1306

# system changes
crontab -e
@reboot sh /home/el3ktra/LilL3x/launch.sh >/home/el3ktra/LilL3x/Logcron/log

wpa_passphrase Lill3x <passprase>
sudo cp ~/LilL3x/install/rclocal /etc/rc.local # if no rc.local
sudo nano /etc/rc.local # put passprhase in local nano file
chmod +x ~/.bashrc
sudo chmod +x /etc/rc.local

# install website -- TODO set base folder
sudo apt-get install apache2
sudo apt-get install php
sudo ln ~/LilL3x/config/html/* /var/www/html/
cp ~/LilL3x/config/config.default ~/LilL3x/config/config.txt

sudo usermod -a -G www-data el3ktra
sudo usermod -a -G www-data www-data

sudo chmod a+x /var/www/html/*.sh
sudo chown root:root /var/www/html/*.sh
sudo chown el3ktra:www-data ~/LilL3x/config ~/LilL3x/config/config.txt
sudo chmod og+rw  ~/LilL3x/config ~/LilL3x/config/config.txt
echo "%www-data ALL=NOPASSWD: /var/www/html/listwifi.sh" | sudo tee -a /etc/sudoers
echo "%www-data ALL=NOPASSWD: /var/www/html/setwifi.sh" | sudo tee -a /etc/sudoers
 #use dedicated sudoers.d file
echo "%www-data ALL=NOPASSWD: /home/el3ktra/LilL3x/config/html/listwifi.sh" | sudo tee /etc/sudoers.d/lill3x
echo "%www-data ALL=NOPASSWD: /home/el3ktra/LilL3x/config/html/setwifi.sh" | sudo tee -a /etc/sudoers.d/lill3x

sudo rm /etc/apache2/sites-enabled/000-default.conf
sudo cp -l ~/LilL3x/install/apache_default.conf /etc/apache2/sites-enabled/000-default.conf
sudo chown root:root /etc/apache2/sites-enabled/000-default.conf
sudo chmod a+rwx /etc/apache2/sites-enabled/000-default.conf
sudo chmod a+rx /home/el3ktra
sudo systemctl restart apache2

# get default wakewords -- #TODO: just grab directory not entire repo!!
cd ~
git clone http://github.com/Picovoice/porcupine.git
cp porcupine/resources/keyword_files/raspberry-pi/* ~/LilL3x/wake
rm -r porcupine

cd ~/LilL3x/
