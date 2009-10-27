#!/usr/bin/env python
import mni
import sys
import optparse

parser = optparse.OptionParser()
parser.add_option("-c", "--calibrate",
        action="store_true", dest="calibrate", default=False,
        help="calibrate the nodes using the CalibrateQuanto applications, before installing.")
(options, args) = parser.parse_args()

m = mni.QuantoMNI()
m.compile()
if options.calibrate:
    sys.stdout.write("Calibrating Nodes: ")
    for n in m.get_nodes():
        sys.stdout.write("%d,%s "%(n.id, n.ip))
    sys.stdout.write("\n\n")
    sys.stdout.flush()

    m.calibrate_all()


sys.stdout.write("Installing application on nodes: ")
for n in m.get_nodes():
    sys.stdout.write("%d,%s "%(n.id, n.ip))
sys.stdout.write("\n")
sys.stdout.flush()

m.install_all()
