ssocr() {
ssocr/ssocr --verbose --debug-image=$2@$1.debug.png --debug-output --threshold=99 --foreground=white --background=black --number-digits 4 rotate $1 r_threshold $2 | tee $2@$1.log
}

ocr() {
	seq 0 5 45 | while read deg ; do
		ssocr $deg $1
	done

	seq 310 5 359 | while read deg ; do
		ssocr $deg $1
	done
}

ls capture/capture*.jpg | while read image ; do
	ocr $image
done

#ls -lS capture/*.log

ls -Ss capture/*@*.log | grep -v '^0' | awk '{ print $2 }' | xargs grep .

if [ ! -e capture/rotation ] ; then
	ls -Ss capture/*@*.log | grep -v '^0' | cut -d@ -f2 | cut -d\. -f1 | sort | uniq > capture/rotation
fi
