camera:
	sudo rm -v /tmp/capture-*
	sudo ./camera.py

cp:
	rm -v capture/capture-* || true
	cp -v /tmp/capture-* capture/

motion:
	rm -vf capture/motion-*
	./motion.py


