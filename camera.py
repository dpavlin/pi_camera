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
state = 'Flip'
valid_states = [ 'Flip', 'Zoom', 'Save', 'Rotate', 'Threshold', 'Digits', 'Exit' ]

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
		in_menu = True
		camera.annotate_text = camera.annotate_text + " [menu]"

	return

# Define the switch
rswitch = RotaryEncoder(PIN_A,PIN_B,BUTTON,switch_event)

print "Rotary encoder pins: %d %d switch: %d" % ( PIN_A, PIN_B, BUTTON )
last_value = 0
frame_nr = 1

camera.annotate_text = state
print state

zoom_axis = 0



ssocr_val = { 'Rotate': 0, 'Threshold': 90, 'Digits': 4 }
ssocr_max = { 'Rotate': 360, 'Threshold': 100, 'Digits': 10 }

overlay = None

def overlay_img(overlay, img = None):

	rotation = ssocr_val['Rotate']

	if ( img == None ):
		img = Image.new('1',(320,200),0)
		if overlay != None:
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

		# make circle
		if rx > ry:
			rx = ry
		if ry > rx:
			ry = rx

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
		overlay = None

	pad = Image.new('RGB', (
		((img.size[0] + 31) // 32) * 32,
		((img.size[1] + 15) // 16) * 16,
		))

	pad.paste(img, (0, 0))

	overlay = camera.add_overlay(pad.tostring(), size=img.size, alpha=128, layer=3) # top of 2 preview

	return overlay


def ssocr(overlay, file):
	command="./ssocr/ssocr.rpi --debug-image=%s.debug.png --foreground=white --background=black --number-digits -1 --threshold=%d rotate %d r_threshold %s 2>&1 > %s.out" % ( file, ssocr_val['Threshold'], ssocr_val['Rotate'], file, file )
	print "# ",command
	camera.annotate_text = command
	subprocess.call(command, shell=True)

	camera.annotate_text = "image"
	img = Image.open(file+'.debug.png')

	overlay = overlay_img(overlay, img)

	with open(file+'.out', 'r') as f:
		out = [line.rstrip('\n') for line in f]
		print "# out", out

	camera.annotate_text = state + ' ' + str(ssocr) + "\n" + str(out)

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
				print "# old state",state,i,mod
				if dv > 0:
					i += 1
				else:
					i -= 1

				try:
					print "# new state",state,i
					state = valid_states[ i ]
				except:
					print "# invalid index ",i,mod
					state = valid_states[0]
			else:
				print "# invalid state",state," in_menu"

			camera.annotate_text = state + " [click to select]"
			print "# new state", state, in_menu

		elif state == "Flip":

			step = 0
			if last_value < v:
				step = +90
			else:
				step = -90
			camera.rotation = camera.rotation + step
			camera.annotate_text = "Flip="+str(camera.rotation)

		elif state == "Zoom":

			if ( overlay != None ):
				camera.remove_overlay(overlay)
				overlay = None

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

		elif state == "Rotate" or state == "Threshold" or state == 'Digits':

			step = dv / 2
			max = ssocr_max[state]
			print "step",step,"max", max
			ssocr_val[state] += step
			ssocr_val[state] = ( max + ssocr_val[state] ) % max
			print "# ",state,ssocr_val[state],step,max
			camera.annotate_text = state + ' ' + str(ssocr_val[state]) + ' ' + str(step)
		
			if state == "Rotate":
				overlay = overlay_img(overlay)
				overlay.alpha = 128


		else:
			print "# ignored rotation in state",state

		print "#XXX",camera.annotate_text
		last_value = v

	if rswitch.button == 1:
		old_in_menu = in_menu
		if in_menu:
			in_menu = False
			camera.annotate_text = state + " [selected]"

		# states which capture clicks when not in_menu
		elif state == "Flip":
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

		save_ocr = False



		# execute selected state after button click (ignore in_menu)
		if old_in_menu == True and in_menu == False:
			print "# first click ", state
			camera.annotate_text = '[' + state + ']'

			if state == 'Save':
				save_ocr = True

		elif state == "Rotate" or state == "Threshold" or state == "Digits":
			save_ocr = True
		elif state == "Save":
			save_ocr = True
			in_menu = True

		elif state == "Exit":
			exit(0)
			in_menu = True
		else:
			print state, " NOT HANDLED"

		if save_ocr:
			#file = "%s/capture-%03d.jpg" % ( os.path.abspath( os.curdir ), frame_nr )
			file = "/tmp/capture-%03d.jpg" % ( frame_nr )
			print "#BUTTON",file
			camera.annotate_text = "" # clean picture annotation before save
			camera.capture( file )
			camera.annotate_text = "Save " + file
			frame_nr += 1

			overlay = ssocr(overlay, file)

	rswitch.button = 0

