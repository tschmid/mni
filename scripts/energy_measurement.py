#!/usr/bin/env python

import sys
import mni
import time
import optparse
import random

parser = optparse.OptionParser()
parser.add_option("-r", "--random",
        action="store",
        type="float",
        dest="random",
        default=-1,
        help="add randomized delays between resets. The supplied parameter\
will the the maximum wait time between consecutive starts.")

parser.add_option("-R", "--reset",
        action="store_true", dest="reset", default=False,
        help="reset the nodes before measuring energy")

parser.add_option("-U", "--userbutton",
        action="store_true", dest="userButton", default=False,
        help="press the usr button after a reset")

parser.add_option("-n",
        action="store", type="int", dest="numMessages", default=580,
        help="number of quanto messages we want to collect at least")

parser.add_option("-o",
        action="store_false", dest="collectData", default=True,
        help="do not collect data from nodes. Just process the data again.")

(cmdOptions, args) = parser.parse_args()

collectData = cmdOptions.collectData

m = mni.QuantoMNI()

print "Loading calibration from file"
m.calibrate_all(readFromFile=True)

i = 0
while i<1:
    i+= 1
    if collectData:
        print "Connecting serial forwarders"
        m.connect_serial_to_file_all(baseFileName="quanto", blocking=False)
        if cmdOptions.reset or cmdOptions.random >0:
            if cmdOptions.random > 0:
                print "Stopping Nodes"
                m.stop_all()
                for n in m.get_nodes():
                    time.sleep(random.random()*cmdOptions.random)
                    print "Starting Node", n.ip, n.id
                    n.start()
            else:
                print "Resetting nodes"
                m.reset_all()

        if cmdOptions.userButton:
            print "Pressing usr button on nodes"
            m.press_usr_all()

        print "Waiting for %d Quanto messages"%(cmdOptions.numMessages,)

        enoughMessages = False
        startTime = time.time()
        while not enoughMessages:
            sys.stdout.write("Rcvd Quanto Msgs at ")
            for n in m.get_nodes():
                sys.stdout.write("node %d: %5d "%(n.id,
                n.get_message_counter()))
            sys.stdout.write("Time: %2.1f\r"%(
                time.time()-startTime))
            sys.stdout.flush()
            enoughMessages = True
            for n in m.get_nodes():
                if n.get_message_counter() < cmdOptions.numMessages:
                    enoughMessages = False
                    break
            time.sleep(1)

        sys.stdout.write("\n")
        m.disconnect_serial_to_file_all()

    try:
        m.parse_quanto_log_all(baseFileName="quanto")
        m.process_quanto_log_all(baseFileName="quanto")
        m.get_energy_per_quanto_state_all(baseFileName="quanto",
                convexOpt=True)
        #m.get_energy_per_quanto_state_all(baseFileName="quanto")
    except mni.ParseError, e:
        print e

    for n in m.get_nodes():
        p = n.statePower
        sys.stdout.write("%.1f Node %d, IP: %s "%(time.time(), n.id, n.ip))
        states = p.keys()
        states.sort()
        for state in states:
            sys.stdout.write("%s %4.2f mW, "%(state, p[state]))
        sys.stdout.write("\n")
        print "Average Power: %.2f mW"%(n.averagePower,)
        sys.stdout.flush()
        print "Always Off States: ", n.alwaysOffStates
        print "Always On States: ", n.alwaysOnStates


