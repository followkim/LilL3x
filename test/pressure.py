#Start by importing all necessary libraries and packages 
import RPi.GPIO as GPIO
import time

pin = 23

#Set the GPIO to BCM Mode
GPIO.setmode(GPIO.BCM)

#Set Pin 4 to be our Sniffer Pin, We want this to be an Input so we set it as such
GPIO.setup(22,GPIO.IN)
GPIO.setup(23,GPIO.IN)

#This variable will be used to determine if pressure is being applied or not
prev_input = 0

#Create a Loop that goes on as long as the script is running
while True:

    #take a reading from the pressure pad (based on the voltage able to get to pin 4)
    input = GPIO.input(22)

    #if the last reading was low and this one high the pressure pad is being pressed!
    if input:
        print("Under Pressure 22")

   #take a reading from the pressure pad (based on the voltage able to get to pin 4)
    input = GPIO.input(23)

    #if the last reading was low and this one high the pressure pad is being pressed!
    if input:
        print("Under Pressure 23")


    #Have a slight pause here, also to avoid spamming the shell with data
    time.sleep(0.10)

