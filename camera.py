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
#camera.video_stabilization = 1

res_steps = [
 	(640,480,30),
 	(1296,972,20),
	(2592,1944,10)
]

camera.resolution = (640,480)
camera.framerate = 30

camera.start_preview()

print "Camera %dx%d" % camera.resolution

in_menu = False
state = 'Flip'
valid_states = [ 'Flip', 'Brightness', 'Zoom', 'Save', 'Crop', 'Rotate', 'Shear', 'Threshold', 'Digits', 'Exit' ]

try:
	with open("/tmp/capture-zoom", 'r') as f:
		zoom = [float(line.rstrip('\n')) for line in f]
		print "# zoom", zoom
		camera.zoom = tuple(zoom)
		print "# camera.zoom", camera.zoom
		in_menu = True
except:
	print "# camera.zoom", camera.zoom

for param in [ 'rotation', 'brightness' ]:
	file = '/tmp/capture-'+param
	try:
		with open(file, 'r') as f:
			d = [line.rstrip('\n') for line in f]
			print "#",file,d
			if param == 'rotation':
				camera.rotation = int(d[0])
				print camera.rotation
			elif param == 'brightness':
				camera.brightness = int(d[0])
			else:
				print 'ERROR',param
	except:
		print "# no", file


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
crop_axis = 0

ssocr_val = { 'Rotate': 0, 'Threshold': 90, 'Digits': -1, 'Shear': 0, 'Crop': [ 0,0,1,1 ] }
ssocr_max = { 'Rotate': 360, 'Threshold': 100, 'Digits': 10, 'Shear':100, 'Brightness':100 }
ssocr_val['Brightness'] = camera.brightness
for k in ssocr_val:
	try:
		with open("/tmp/capture-ssocr-"+k, 'r') as f:
			lines = [line.rstrip('\n') for line in f]
			ssocr_val[k] = int(lines[0])
			print "# /tmp/capture-ssocr-"+k+"="+str(ssocr_val[k])
	except:
		print "# default", k, ssocr_val[k]


overlay = None

def overlay_img(overlay, img = None):

	if ( img == None ):
		img = Image.new('1',(320,200),0)
		if overlay != None:
			overlay.opacity = 128

		draw = ImageDraw.Draw(img) 


		if state == 'Rotate':

			rotation = ssocr_val['Rotate']

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


		elif state == 'Shear':
			s = ssocr_val['Shear']
			dx = int(camera.resolution[0] * s / 100 / 4)

			draw.line([( img.size[0]/2+dx,0 ),( img.size[0]/2-dx, img.size[1] )], fill=1, width=1)


		elif state == 'Crop':
			c = ssocr_val['Crop'][crop_axis]

			if crop_axis == 0 or crop_axis == 2:
				c = c * img.size[0]
				draw.line([( c, 0 ),( c, img.size[1] )], fill=1, width=1)
			else:
				c = c * img.size[1]
				draw.line([( 0, c ),( img.size[0], c )], fill=1, width=1)



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
	opt=""
	if ( ssocr_val['Crop'] != ( 0,0,1,1 ) ):
		c = ssocr_val['Crop']
		w,h = camera.resolution
		opt+=" crop %d %d %d %d" % ( int(c[0]*w), int(c[1]*h), int(c[2]*w), int(c[3]*h) )
	if ( ssocr_val['Shear'] != 0):
		opt+=" shear %d" % ( int(camera.resolution[0] * ssocr_val['Shear'] / 100 ) )
	if ( ssocr_val['Rotate'] != 0):
		opt+=" rotate %d" % ( ssocr_val['Rotate'] )

	command="./ssocr/ssocr.rpi --debug-image=%s.debug.png --foreground=white --background=black --number-digits -1 --threshold=%d r_threshold %s %s 2>&1 > %s.out" % ( file, ssocr_val['Threshold'], opt, file, file )
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
			i = None
			if state in valid_states:
				i = valid_states.index(state)
				mod = len(valid_states)
				print "# old state",state,i,mod
				if dv > 0:
					i += 1
				else:
					i -= 1


				# cycle
				if i < 0:
					i = mod - 1
				if i >= mod:
					i = 0

					i = 0
			else:
				print "# invalid state",state," in_menu"

			state = valid_states[i]
			print "# new state",state

			out = ''
			for s in valid_states:
				if s == state:
					out += '*' + state + '* '
				else:
					out += ' ' + s + '  '


			camera.annotate_text = out + '\n'
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


		elif state == "Crop":

			step = dv * 0.01
			print "step",step

			ssocr_val['Crop'][crop_axis] -= step # left = dec, right = inc
			print "#Crop",ssocr_val['Crop']

			if ssocr_val['Crop'][crop_axis] < 0:
				ssocr_val['Crop'][crop_axis] = 0
				step = 'MIN'

			max = 1
			if ssocr_val['Crop'][crop_axis] > max:
				ssocr_val['Crop'][crop_axis] = max 
				step = 'MAX'

			camera.annotate_text = "Crop %d %.3f %s" % ( crop_axis, ssocr_val['Crop'][crop_axis],step )
			overlay = overlay_img(overlay)
			overlay.alpha = 128

		elif state in ssocr_max.keys():

			step = dv / 2
			max = ssocr_max[state]
			print "step",step,"max", max
			ssocr_val[state] += step
			ssocr_val[state] = ( max + ssocr_val[state] ) % max
			print "# ",state,ssocr_val[state],step,max
			camera.annotate_text = state + ' ' + str(ssocr_val[state]) + ' ' + str(step)
		
			if state in [ 'Rotate', 'Shear' ]:
				overlay = overlay_img(overlay)
				overlay.alpha = 128

			if state == 'Brightness':
				print 'XXX', camera.brightness, state
				camera.brightness = int(ssocr_val[state]);
				print 'XXX', camera.brightness

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

				z = camera.zoom
				zx = z[2] - z[0]
				zy = z[3] - z[1]
				print 'XXX',zx,zy

				new_res = res_steps[ int(zx*3) - 1 ]
				if ( camera.resolution != new_res ):
					camera.stop_preview()
					camera.resolution = (new_res[0],new_res[1])
					camera.framerate = new_res[2]
					print "Camera %dx%d" % camera.resolution
					camera.start_preview()


			else:
				camera.annotate_text = "Zoom %d %.3f" % ( zoom_axis, camera.zoom[zoom_axis] )

		elif state == "Crop":
			crop_axis += 1

			if crop_axis > 3:
				state = "Save"
				in_menu = True
				camera.annotate_text = state
				# save camera crop to file
				print "# /tmp/capture-ssocr-crop", camera.crop
				with open("/tmp/capture-ssocr-crop", 'w') as f:
				    for s in ssocr_val['Crop']:
					f.write(str(s) + '\n')
				crop_axis = 0
			else:
				camera.annotate_text = "Crop %d %.3f" % ( crop_axis, ssocr_val['Crop'][crop_axis] )


		save_ocr = False



		# execute selected state after button click (ignore in_menu)
		if old_in_menu == True and in_menu == False:
			print "# first click ", state
			camera.annotate_text = '[' + state + ']'

			if state == 'Save':
				save_ocr = True

		elif state in ssocr_max.keys():
			save_ocr = True
			with open("/tmp/capture-ssocr-"+state, 'w') as f:
				f.write(str(ssocr_val[state])+'\n')
			in_menu = True

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

