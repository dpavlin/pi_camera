#!/usr/bin/env python
#
# Raspberry Pi Rotary Test Encoder Class
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses a standard rotary encoder with push switch
#

import sys
import time
from rotary_class import RotaryEncoder

# Define GPIO inputs
PIN_A = 27
PIN_B = 22
BUTTON = 17


import picamera

camera = picamera.PiCamera()
camera.start_preview()
camera.annotate_text = "Ready"

camera.resolution = (640, 480)
camera.framerate = 24

print "Camera %dx%d" % camera.resolution

# This is the event callback routine to handle events
def switch_event(event):
	t = time.clock()
	if event == RotaryEncoder.CLOCKWISE:
		print t,"Clockwise"
		camera.annotate_text = camera.annotate_text + ">"
	elif event == RotaryEncoder.ANTICLOCKWISE:
		print t,"Anticlockwise"
		camera.annotate_text = camera.annotate_text + "<"
	elif event == RotaryEncoder.BUTTONDOWN:
		print t,"Button down"
	elif event == RotaryEncoder.BUTTONUP:
		print t,"Button up"

	return

# Define the switch
rswitch = RotaryEncoder(PIN_A,PIN_B,BUTTON,switch_event)

print "Rotary encoder pins: %d %d switch: %d" % ( PIN_A, PIN_B, BUTTON )
last_value = 0
while True:
	time.sleep(0.5)
	if last_value != rswitch.value:
		print "# rotary encoder = ",rswitch.value

		step = 0
		if last_value < rswitch.value:
			step = +90
		else:
			step = -90
		camera.rotation = camera.rotation + step
		camera.annotate_text = "Rotation="+str(camera.rotation)
		print "#NEW",camera.annotate_text

		last_value = rswitch.value

