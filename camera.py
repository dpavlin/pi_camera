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
#camera.video_stabilization = 1

camera.resolution = (640, 480)
camera.framerate = 30

print "Camera %dx%d" % camera.resolution

try:
	with open("/tmp/capture-zoom", 'r') as f:
		zoom = [float(line.rstrip('\n')) for line in f]
		print "# camera.zoom", camera.zoom
		camera.zoom = tuple(zoom)
		print "# camera.zoom", camera.zoom
except:
	print "# camera.zoom", camera.zoom

try:
	with open("/tmp/capture-rotation", 'r') as f:
		rotation = [line.rstrip('\n') for line in f]
		camera.rotation = rotation
		print "# camera.rotation", camera.rotation
except:
	print "# camera.rotation", camera.rotation


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

state = 'Rotation'
valid_states = [ 'Rotation', 'Zoom', 'Save', 'Exit' ]
camera.annotate_text = state

zoom_axis = 0

while True:
	time.sleep(0.5)
	if last_value != rswitch.value:
		v = rswitch.value
		dv = last_value - v
		print "# rotary encoder = ",v, "dv=",dv

		if state == "Rotation":

			step = 0
			if last_value < v:
				step = +90
			else:
				step = -90
			camera.rotation = camera.rotation + step
			camera.annotate_text = "Rotation="+str(camera.rotation)

		elif state == "Zoom":

			step = dv * 0.01
			print "step",step

			z = list(camera.zoom)
			print "#zoom",z
			z[zoom_axis] -= step # left = dec, right = inc

			if z[zoom_axis] < 0:
				z[zoom_axis] = 0
				step = 'MIN'

			max = 1
			if zoom_axis == 2:
				max = 1 - z[0]
			if zoom_axis == 3:
				max = 1 - z[1]
			if z[zoom_axis] > max:
				z[zoom_axis] = max 
				step = 'MAX'

			camera.zoom = tuple(z)
			camera.annotate_text = "Zoom %d %.3f %s" % ( zoom_axis, camera.zoom[zoom_axis],step )
			print "#zoom",camera.zoom,z

		elif state in valid_states:
			i = valid_states.index(state)
			mod = len(valid_states)
			if dv > 0:
				state = valid_states[ i + 1 % mod ]
			else:
				state = valid_states[ i - 1 % mod ]
		else:
			print "# ignored rotation in state",state

		print "#XXX",camera.annotate_text
		last_value = v

	if rswitch.button == 1:
		if state == "Rotation":
			state = "Zoom"
			camera.annotate_text = state 
			print "# /tmp/capture-rotation", camera.rotation
			with open("/tmp/capture-rotation", 'w') as f:
				f.write(str(camera.rotation) + '\n')

		elif state == "Zoom":
			zoom_axis += 1
			
			if zoom_axis > 3:
				state = "Save"
				camera.annotate_text = state
				# save camera zoom to file
				print "# /tmp/capture-zoom", camera.zoom
				with open("/tmp/capture-zoom", 'w') as f:
				    for s in camera.zoom:
				        f.write(str(s) + '\n')
				zoom_axis = 0
			else:
				camera.annotate_text = "Zoom %d %.3f" % ( zoom_axis, camera.zoom[zoom_axis] )

		elif state == "Save":
			#file = "%s/capture-%03d.jpg" % ( os.path.abspath( os.curdir ), frame_nr )
			file = "/tmp/capture-%03d.jpg" % ( frame_nr )
			print "#BUTTON",file
			camera.annotate_text = "" # clean picture annotation before save
			camera.capture( file )
			camera.annotate_text = "Save " + file
			frame_nr += 1

		elif state == "Exit":
			exit

	rswitch.button = 0

