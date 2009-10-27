import unittest
import ConfigParser
import os
import node

from mni import *

class TestQuantoMNI(unittest.TestCase):

    def test_calibrate(self):
        fileName = "config.ini"
        f = file(fileName, 'w')
        f.write("""
[Nodes]
numNodes: 1
type: QuantoTestbedMote
makeCmd: make epic quanto

[Node1]
id: 1
ip: 172.17.6.104
serial: /dev/ttyrd00
installCmd: make epic quanto reinstall,1 bsl,/dev/ttyrd00
""")
        f.flush()
        f.close()

        m = QuantoMNI()
        self.assertTrue(m)

        # calibrate the nodes including compilation and installation of the
        # calibration application. Write the result into a config file
        m.calibrate_all(doInstallCompile=False)

        a = []
        for n in m.get_nodes():
            a.append(n.get_energy(47.75, 1.0))
            a.append(n.get_energy(470.75, 1.0))
            a.append(n.get_energy(460.75, 1.0))
            a.append(n.get_energy(47000.75, 1.0))

        # now, read the calibration from file
        m.calibrate_all(readFromFile=True)

        # check if the results are the same
        for n in m.get_nodes():
            self.assertTrue(n.get_energy(47.75, 1.0) in a)
            self.assertTrue(n.get_energy(470.75, 1.0) in a)
            self.assertTrue(n.get_energy(460.75, 1.0) in a)
            self.assertTrue(n.get_energy(47000.75, 1.0) in a)



        os.remove(fileName)

if __name__ == "__main__":
    unittest.main()
