#!/bin/bash
source /home/el3ktra/LilL3x/bin/activate

sudo rm /var/www/html/*
sudo ln ~/LilL3x/config/html/* /var/www/html/
sudo chmod a+x /var/www/html/*.sh
sudo chown root:root /var/www/html/*.sh
sudo chmod a+x /home/el3ktra ~/LilL3x/config  ~/LilL3x/training  ~/LilL3x/picts  ~/LilL3x/log



