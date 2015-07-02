# oil-tank-monitor
A Python script to use a HRS04 sonar sensor and Raspberry Pi to measure the volume of heating oil remaining in an oil tank. The value is sent to a Domoticz virtual device. 

The script sends N pings from a HRS04 ultrasonic sensor connected to the GPIO pins on a Raspberry Pi. Iit measures the time between sending and receiving the ping. If we don't get a successful ping, take the measurement again.

It then takes each ping time and calculates the distance to the top of the oil, factoring in the current air temperature for speed of sound calculations. Each calculated distance to the top of the oil is added to an array of distances.

The array is sorted in ascending order and outliers eliminated by keeping only the "middle" third of distances in the array. An average is taken of the middle third of distances. The averaged oil tank space is subtracted from the height of the tank in order to calculate the height of the oil. With the height of the oil the percentage of oil remaining is calculated. 

Right now the oil tank capacity hard-coded and I fudge the percentage of oil remaining from that, without considering the tank shape. The next thing to do is to add accurate calculations of oil volume remaining in my tank based on the shape of the tank. I have a very odd shaped tank, so this is going to be tricky!

Finally the script sends the value to a virtual device on a Domoticz home automation server, where it is plotted on a graph and can be alerted on.
