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
import os

from rotary_class import RotaryEncoder

# Define GPIO inputs
PIN_A = 27
PIN_B = 22
BUTTON = 17


import picamera

camera = picamera.PiCamera()
camera.start_preview()

camera.resolution = (640, 480)
camera.framerate = 30

print "Camera %dx%d" % camera.resolution

# This is the event callback routine to handle events
def switch_event(event):
	t = time.clock()
	if event == RotaryEncoder.CLOCKWISE:
		#print t,"Clockwise"
		camera.annotate_text = camera.annotate_text + ">"
	elif event == RotaryEncoder.ANTICLOCKWISE:
		#print t,"Anticlockwise"
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
frame_nr = 1

state = 'Rotate'
camera.annotate_text = state

zoom_axis = 0

while True:
	time.sleep(0.5)
	if last_value != rswitch.value:
		v = rswitch.value
		dv = last_value - v
		print "# rotary encoder = ",v, "dv=",dv

		if state[:3] == "Rot":

			step = 0
			if last_value < v:
				step = +90
			else:
				step = -90
			camera.rotation = camera.rotation + step
			camera.annotate_text = "Rotation="+str(camera.rotation)

		if state[:3] == "Zoo":

			step = dv / 2 * 0.05
			print "step",step

			z = list(camera.zoom)
			z[zoom_axis] -= step # left = dec, right = inc

			camera.zoom = tuple(z)
			camera.annotate_text = "Zoom %d %.3f" % ( zoom_axis, camera.zoom[zoom_axis] )

		else:
			print "# ignored rotation in state",state

		print "#XXX",camera.annotate_text
		last_value = v

	if rswitch.button == 1:
		if state[:3] == "Rot":
			state = "Zoom"
			camera.annotate_text = state 

		elif state[:3] == "Zoo":
			zoom_axis += 1
			if zoom_axis > 3:
				state = "Save"
				camera.annotate_text = state
			else:
				camera.annotate_text = "Zoom %d %.3f" % ( zoom_axis, camera.zoom[zoom_axis] )

		elif state[:3] == "Sav":
			#file = "%s/capture-%03d.jpg" % ( os.path.abspath( os.curdir ), frame_nr )
			file = "/tmp/capture-%03d.jpg" % ( frame_nr )
			print "#BUTTON",file
			camera.annotate_text = "" # clean picture annotation before save
			camera.capture( file )
			camera.annotate_text = "Save " + file
			frame_nr += 1

	rswitch.button = 0

