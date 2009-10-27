#!/usr/bin/env python

import sys
import mni
import time

m = mni.QuantoMNI()

print "stopping nodes:"
for n in m.get_nodes():
    sys.stdout.write("Node %s\n"%(n.ip,))

m.stop_all()

