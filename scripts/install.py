#!/usr/bin/env python
from mni import mni
import sys
import optparse

m = mni.MNI()
m.compile()

sys.stdout.write("Installing application on nodes: ")
for n in m.get_nodes():
    sys.stdout.write("%d,%s "%(n.id, n.serial))
sys.stdout.write("\n")
sys.stdout.flush()

m.install_all()
