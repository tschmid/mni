#!/usr/bin/env python

import sys
import mni
import time
import optparse
import time
import random

parser = optparse.OptionParser()
parser.add_option(
        "-n", "--node",
        action="store",
        type="int",
        dest="nodeid",
        default=-1,
        help="id of the node that should be put in serial mode")

(options, args) = parser.parse_args()

m = mni.QuantoMNI()

if options.nodeid != -1 and options.nodeid >= 0:
    for n in m.get_nodes():
        if n.id == options.nodeid:
            print "Pushing user button on node %d"%(n.id)
            n.push_usr()
            n.release_usr()
            sys.exit(0)
    print "Couldn't find node with id %d in your configuration!"%(options.nodeid)
else:
    print "Node ID invalid!"

