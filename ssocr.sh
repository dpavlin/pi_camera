ssocr() {
ssocr/ssocr --verbose --debug-image --debug-output --threshold=99 --foreground=white --background=black --number-digits 4 rotate $1 r_threshold $2 | tee $2@$1.log
}

ocr() {
	ssocr 0 $1
	ssocr 10 $1
	ssocr 20 $1
	ssocr 30 $1

	ssocr 355 $1
	ssocr 350 $1
	ssocr 345 $1
	ssocr 340 $1
	ssocr 335 $1
	ssocr 330 $1
	ssocr 325 $1
	ssocr 320 $1
	ssocr 315 $1
	ssocr 310 $1
}

ls capture/capture*.jpg | while read image ; do
	ocr $image
done

#ls -lS capture/*.log

ls -Ss capture/*@*.log | grep -v '^0' | awk '{ print $2 }' | xargs grep .
