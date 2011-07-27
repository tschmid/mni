#!/bin/bash

set -u

NODE_NAME=""

while [ -z "$NODE_NAME" ]; do
	read -p "What is the name of this node (e.g rs): " NODE_NAME
done

while true; do
	read -p "What is the IP of this node: " NODE_IP
	NODE_IP=`gethostip -d $NODE_IP`
	if [ $? -eq 0 ]; then break; fi
done

set -x
sudo /usr/bin/dgrp/config/dgrp_cfg_node init -v -v -e never $NODE_NAME $NODE_IP 1 > /dev/null
sudo chgrp dialout "/dev/tty"$NODE_NAME"00"
sudo chmod g+rwx "/dev/tty"$NODE_NAME"00"
set +x

if [ -w "config.ini" ]; then
	while true; do
		read -p "config.ini found, add this node? (default Y): " yn
		if [ -z $yn ]; then break; fi
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit;;
			* ) echo "Please answer yes or no.";;
		esac
	done

	NUM_NODES=`grep numNodes: config.ini | awk '{n = substr($0, match($0, /[0-9]+/), RLENGTH) + 1; sub(/[0-9]+/, n); print }'`
	NODE_NUMBER=`grep '\[Node[0-9]*\]' config.ini | tail -n 1 | awk '{n = substr($0, match($0, /[0-9]+/), RLENGTH) + 1; sub(/[0-9]+/, n); print }'`
	NODE_ID=`grep 'id:' config.ini | tail -n 1 | awk '{n = substr($0, match($0, /[0-9]+/), RLENGTH) + 1; sub(/[0-9]+/, n); print }'`
	if [ `grep installCmd config.ini | uniq | wc -l` -gt 1 ]; then
		echo "Ambiguous installCmd, cannot auto-add - failing..."
		exit
	fi
	NODE_CMD=`grep installCmd config.ini | uniq`
	read -p "Select 'timeoffset' (default 0): " NODE_TIME
	if [ -z "$NODE_TIME" ]; then NODE_TIME=0; fi

	sed -i "s/`grep numNodes: config.ini`/$NUM_NODES/" config.ini
	sed -i '$ d' config.ini
	echo -ne "$NODE_NUMBER\n$NODE_ID\nip: $NODE_IP\n" >> config.ini
	echo -ne "serial: /dev/tty"$NODE_NAME"00\n" >> config.ini
	echo -ne "$NODE_CMD\ntimeoffset: $NODE_TIME\n" >> config.ini
	echo -ne "\n\n" >> config.ini

	echo "   * $NODE_NUMBER Added to config.ini"
fi
