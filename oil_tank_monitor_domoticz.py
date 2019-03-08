#!/usr/bin/python

# Libs
import time
import RPi.GPIO as GPIO
import urllib

# Defaults
number_of_pings = 30
oil_tank_height = 98
oil_tank_length = 178
oil_tank_width = 138
oil_tank_capacity = 1200
ping_timeout = 0.02
domoticz_device_idx = 13

# Take measurements by pinging the oil from HRS04 sensor and put in an array of distances. Return oil_tank_space
def measure():
    distances = []
    for ping in range(1, number_of_pings):
        complete=False
        while not complete:
	    # Send 5us pulse to trigger
            GPIO.output(GPIO_TRIGGER, False)
            time.sleep(0.000002)
            GPIO.output(GPIO_TRIGGER, True)
            time.sleep(0.000005)
            GPIO.output(GPIO_TRIGGER, False)
            start = time.time()

            successful_ping=True
            read_time=time.time()
            ping_start_time=0
            ping_end_time=0
            while GPIO.input(GPIO_ECHO)==0 and successful_ping:
                ping_start_time = time.time()
                if (ping_start_time-read_time > ping_timeout):
                    successful_ping=False

            if successful_ping:
                read_time=time.time()
                while GPIO.input(GPIO_ECHO)==1 and successful_ping:
                    ping_end_time=time.time()
                    if (ping_end_time-read_time > ping_timeout):
                        successful_ping=False
            else:
                continue

	    # If we don't get a successful ping, take the measurement again
            if not successful_ping:
                continue

	    # If we do get a successful ping, start distance calculations
            if successful_ping:
                # Calculate pulse length
                elapsed = ping_end_time - ping_start_time

                # Get currrent air temp for speed of sound calculation
                # temperature = tmp102.read()
                temperature = 20

                # Calculate current speed of sound based on air temp
                sound_speed = 331.3 + (0.6 * temperature)

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
    third = int(len(distances) / 3)
    two_thirds = third * 2

    # Find the distances in the middle 33%. Discard outliers that are too large
    middle_distances = distances[third:two_thirds]

    # Get the median by using reduce on the 'middle' range of distances
    oil_tank_space = (reduce(add, middle_distances)) / len(middle_distances)

    # Device accurate to 1cm so round the value to nearest cm
    oil_tank_space = round(oil_tank_space)

    return oil_tank_space

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
print "Oil depth is {} cm".format(oil_level)
percent_full = (oil_level / oil_tank_height) * 100
print "Oil tank is {}% full".format(percent_full)
oil_litres_remaining = oil_tank_capacity * (oil_level / oil_tank_height)
print "There is {} litres of oil in the tank".format(oil_litres_remaining)

# Send percentage remaining value to virtual device in Domoticz
urllib.urlopen("http://192.168.1.1:8080/json.htm?type=command&param=udevice&idx={}&nvalue=0&svalue={}".format( domoticz_device_idx, percent_full ))

# GPIO reset
GPIO.cleanup()
