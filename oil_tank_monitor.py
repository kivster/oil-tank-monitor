#!/usr/bin/python

# Libs
import time
import RPi.GPIO as GPIO
import urllib

# Constants
number_of_pings = 30
oil_tank_height = 98
oil_tank_length = 178
oil_tank_width = 138
oil_tank_capacity = 1200
oil_burn_rate = 1.41
ping_timeout = 0.02
domoticz_device_idx = 13

def measure():
    distances = []
    for ping in range(1, number_of_pings):
        complete=False
        while not complete:
	    # Send 5us (microsecond) pulse to trigger
            GPIO.output(GPIO_TRIGGER, False)
            time.sleep(0.000002)
            GPIO.output(GPIO_TRIGGER, True)
            time.sleep(0.000005)
            GPIO.output(GPIO_TRIGGER, False)
            start = time.time()

            goodping=True
            watchtime=time.time()
            ping_start_time=0
            ping_end_time=0
            while GPIO.input(GPIO_ECHO)==0 and goodping:
                ping_start_time = time.time()
                if (ping_start_time-watchtime > ping_timeout):
                    goodping=False

            if goodping:
                watchtime=time.time()
                while GPIO.input(GPIO_ECHO)==1 and goodping:
                    ping_end_time=time.time()
                    if (ping_end_time-watchtime > ping_timeout):
                        goodping=False
            else:
                continue

            if not goodping:
                continue

            if goodping:
                # Calculate pulse length
                elapsed = ping_end_time - ping_start_time

                # Get currrent air temp for speed of sound calculation
                # air_temp = tmp102.read()
                air_temp = 20

                # Calculate current speed of sound based on air temp
                sound_speed = 331.3 + (0.6 * air_temp)

                # Distance is pulse length multipled by the speed of sound
                # Divide by two to avoid measuring distance twice
                # Multiply by 100 for meters to centimeters
                distance = ((elapsed * sound_speed ) / 2) * 100

                # Add distance to the oil value to the array
                distances.append(distance)
                time.sleep(0.02)

                complete=True

            time.sleep(0.05)

    # Sort the array of distances
    distances.sort

    # Chunk into thirds
    onethird = int(len(distances) / 3)
    twothirds = onethird * 2

    # Find the distances in the middle 33%. Discard outliers that are too large
    mid_distances = distances[onethird:twothirds]

    # Get the median by using reduce on the 'middle' range of distances
    tank_air_space = (reduce(add, mid_distances)) / len(mid_distances)

    # Device accurate to 1cm so round the value to nearest cm
    tank_air_space = round(tank_air_space)

    return tank_air_space

# For reduce add function later on to calculate sum of distances for averaging
# Sum of first two items + the next item
def add(x,y): return x+y

def get_fill_height():
    # Returns how high the oil is in the tank
    air_space = measure()
    oil_level = oil_tank_height - air_space
    print "Oil level is ", oil_level, " cm"
    return oil_level

# Main script stuff here
# Use BCM GPIO references
GPIO.setmode(GPIO.BCM)

# Define GPIO to use on Pi
GPIO_TRIGGER = 23
GPIO_ECHO    = 24

print "Pinging oil level..."

# Set pins as output/trigger and input/echo
GPIO.setup(GPIO_TRIGGER,GPIO.OUT)
GPIO.setup(GPIO_ECHO,GPIO.IN)

# Set trigger as off by default
GPIO.output(GPIO_TRIGGER, False)

# Rest
time.sleep(0.5)

# Various oil calculations
distance = measure()
oil_level = oil_tank_height - distance
print "Oil remaining is {} cm".format(oil_level)
percent_full = (oil_level / oil_tank_height) * 100
print "Tank is {} percent full".format(percent_full)
oil_litres_remaining = oil_tank_capacity * (oil_level/oil_tank_height)
print "There is {} litres of oil remaining".format(oil_litres_remaining)
oil_hours_remaining = oil_litres_remaining / oil_burn_rate
print "There is {} hours of oil remaining".format(oil_hours_remaining)

# Send percentage remaining value to virtual device in Domoticz
urllib.urlopen("http://192.168.1.1:8080/json.htm?type=command&param=udevice&idx={}&nvalue=0&svalue={}".format( domoticz_device_idx, percent_full ))

# GPIO reset
GPIO.cleanup()
