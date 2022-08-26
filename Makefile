default:

install:
	sudo cp conf/98-usb.rules /etc/udev/rules.d
	sudo udevadm control --reload-rules
