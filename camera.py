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
import StringIO
import subprocess
from PIL import Image, ImageDraw
import math

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

in_menu = False
state = 'Rotation'
valid_states = [ 'Rotation', 'Zoom', 'Save', 'Exit' ]

try:
	with open("/tmp/capture-zoom", 'r') as f:
		zoom = [float(line.rstrip('\n')) for line in f]
		print "# zoom", zoom
		camera.zoom = tuple(zoom)
		print "# camera.zoom", camera.zoom
		in_menu = True
except:
	print "# camera.zoom", camera.zoom

try:
	with open("/tmp/capture-rotation", 'r') as f:
		rotation = [line.rstrip('\n') for line in f]
		camera.rotation = rotation[0]
		print "# camera.rotation", camera.rotation
		in_menu = True
		state = 'Save'
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

camera.annotate_text = state
print state

zoom_axis = 0



ssocr_rotate = 0

overlay = None
overlay_img = None

def overlay_rotation(overlay, img, rotation):

	if ( img == None ):
		img = Image.new('1',(320,200),0)
		overlay.opacity = 128

	draw = ImageDraw.Draw(img) 
	bbox = (img.size[0] / 4,img.size[1] / 4,img.size[0] / 4 * 3,img.size[1] / 4 * 3)
	draw.arc(bbox, 0, rotation, 1)

	bbox = (0,0,img.size[0],img.size[1])

	# radians
	a = ( 360 - rotation + 90 % 360 ) * math.pi / 180

	# ellips radii
	rx = (bbox[2] - bbox[0]) / 2
	ry = (bbox[3] - bbox[1]) / 2

	# box centre
	cx = bbox[0] + rx
	cy = bbox[1] + ry

	# x,y centre
        x = cx + math.cos(a) * rx
        y = cy + math.sin(a) * ry

	draw.line([(x,y),(cx,cy)], fill=1, width=1)

	d90 = math.pi/2
	draw.line([(cx,cy),(cx + math.cos(a+d90) * rx,cy + math.sin(a+d90) * ry)], fill=1, width=2)
	draw.line([(cx,cy),(cx + math.cos(a-d90) * rx,cy + math.sin(a-d90) * ry)], fill=1, width=3)

        # derivatives
        dx = -math.sin(a) * rx / (rx+ry)
        dy = math.cos(a) * ry / (rx+ry)

	l = 4
	draw.line([(x-dx*l,y-dy*l), (x+dx*l, y+dy*l)], fill=1, width=3)


	if ( overlay != None ):
		camera.remove_overlay(overlay)

	pad = Image.new('RGB', (
		((img.size[0] + 31) // 32) * 32,
		((img.size[1] + 15) // 16) * 16,
		))

	pad.paste(img, (0, 0))

	overlay = camera.add_overlay(pad.tostring(), size=img.size, alpha=128, layer=3) # top of 2 preview

	return overlay


def ssocr(overlay, file, rotate):
	command="./ssocr/ssocr.rpi --debug-image=%s.debug.png --foreground=white --background=black --number-digits 3 rotate %d r_threshold %s 2>&1 > %s.out" % ( file, ssocr_rotate, file, file )
	print "# ",command
	camera.annotate_text = command
	subprocess.call(command, shell=True)

	camera.annotate_text = "image"
	img = Image.open(file+'.debug.png')
	overlay_img = img

	overlay = overlay_rotation(overlay, img, rotate)

	with open(file+'.out', 'r') as f:
		out = [float(line.rstrip('\n')) for line in f]
		print "# out", out

	camera.annotate_text = state + ' ' + str(ssocr_rotate) + ' ' + str(out)

	return overlay

while True:
	time.sleep(0.5)
	if last_value != rswitch.value:
		v = rswitch.value
		dv = last_value - v
		print "# rotary encoder = ",v, "dv=",dv

		if in_menu:
			if state in valid_states:
				i = valid_states.index(state)
				mod = len(valid_states)
				if dv > 0:
					i += 1
				else:
					i -= 1

				try:
					state = valid_states[ i ]
				except:
					print "# invalid index ",i,mod
					state = valid_states[0]

			camera.annotate_text = state + " [click to select]"
			print "# new state", state, in_menu

		elif state == "Rotation":

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

			try:
				camera.zoom = tuple(z)
				camera.annotate_text = "Zoom %d %.3f %s" % ( zoom_axis, camera.zoom[zoom_axis],step )
				print "#zoom",camera.zoom,z
			except:
				print "# invalid zoom ",z

		elif state == "OCR":

			step = dv / 2
			print "step",step
			ssocr_rotate += step
			ssocr_rotate = ( 360 + ssocr_rotate ) % 360
			print "# OCR",step,ssocr_rotate
			camera.annotate_text = "OCR " + str(ssocr_rotate) + ' ' + str(step)
			overlay.alpha = 128

			overlay = overlay_rotation(overlay, overlay_img, ssocr_rotate)

			#state = 'Save'
			#rswitch.button = 1 # fake click to save now

		else:
			print "# ignored rotation in state",state

		print "#XXX",camera.annotate_text
		last_value = v

	if rswitch.button == 1:
		if in_menu:
			in_menu = False
			camera.annotate_text = state + " [selected]"

		# states which capture clicks when not in_menu
		elif state == "Rotation":
			state = "Zoom"
			camera.annotate_text = state 
			print "# /tmp/capture-rotation", camera.rotation
			with open("/tmp/capture-rotation", 'w') as f:
				f.write(str(camera.rotation) + '\n')

		elif state == "Zoom":
			zoom_axis += 1
			
			if zoom_axis > 3:
				state = "Save"
				in_menu = True
				camera.annotate_text = state
				# save camera zoom to file
				print "# /tmp/capture-zoom", camera.zoom
				with open("/tmp/capture-zoom", 'w') as f:
				    for s in camera.zoom:
					f.write(str(s) + '\n')
				zoom_axis = 0
			else:
				camera.annotate_text = "Zoom %d %.3f" % ( zoom_axis, camera.zoom[zoom_axis] )


		# execute selected state after button click (ignore in_menu)
		if state == "Save" or state == "OCR":
			#file = "%s/capture-%03d.jpg" % ( os.path.abspath( os.curdir ), frame_nr )
			file = "/tmp/capture-%03d.jpg" % ( frame_nr )
			print "#BUTTON",file
			camera.annotate_text = "" # clean picture annotation before save
			camera.capture( file )
			camera.annotate_text = "Save " + file
			frame_nr += 1

			overlay = ssocr(overlay, file, ssocr_rotate)

			state = 'OCR'

		elif state == "Exit":
			exit(0)
			in_menu = True
		else:
			print "# no code for button", state

	rswitch.button = 0

