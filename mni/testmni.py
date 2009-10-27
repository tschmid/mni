import unittest
import ConfigParser
import os
import node

from mni import *

# set the following two IP addresses to check for proper MNI working!

class TestMNI(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_non_existing_configuration_file(self):
        self.assertRaises(IOError, MNI, configFile="nonexistingfile")

    def test_read_wrong_config_file(self):
        fileName = "config.ini"
        f = file(fileName, 'w')
        f.write(" ")
        f.close()

        self.assertRaises(ConfigParser.NoSectionError, MNI)

        f = file(fileName, 'w')
        f.write("[Nodes]")
        f.close()

        self.assertRaises(ConfigParser.NoOptionError, MNI)

        f = file(fileName, 'w')
        f.write("""
[Nodes]
numNodes: 1

[Node1]
id: 1
""")

        f.close()

        self.assertRaises(ConfigParser.NoOptionError, MNI)

        f = file(fileName, 'w')
        f.write("""
[Nodes]
numNodes: 1
type: Node

[Node1]
id: 1
""")

        f.close()

        self.assertRaises(ConfigParser.NoOptionError, MNI)


        f = file(fileName, 'w')
        f.write("""
[Nodes]
numNodes: 4
type: Node
makeCmd: make epic
""")

        f.close()

        self.assertRaises(ConfigParser.NoSectionError, MNI)

        f = file(fileName, 'w')
        f.write("""
[Nodes]
numNodes: 1
type: NonExistingClass
makeCmd: make epic

[Node1]
id: 1
""")

        f.close()

        self.assertRaises(AttributeError, MNI)

        os.remove(fileName)


    def test_read_configuration_file(self):
        fileName = "config.ini"
        f = file(fileName, 'w')
        f.write("""
[Nodes]
numNodes: 4
type: QuantoTestbedMote
makeCmd: make epic

[Node1]
id: 1
ip: 172.17.6.102
serial: /dev/ttyrb00
installCmd: make epic miniprog reinstall,1 bsl,/dev/ttyrb00

[Node2]
id: 2
ip: 172.17.6.103
serial: /dev/ttyrc00
installCmd: make epic miniprog reinstall,2 bsl,/dev/ttyrc00

[Node3]
id: 3
ip: 172.17.6.104
serial: /dev/ttyrd00
installCmd: make epic miniprog reinstall,3 bsl,/dev/ttyrd00

[Node4]
id: 4
ip: 172.17.6.105
serial: /dev/ttyre00
installCmd: make epic miniprog reinstall,4 bsl,/dev/ttyre00
""")
        f.flush()
        f.close()

        mni = MNI()
        self.assertTrue(len(mni.get_nodes()) == 4)

        self.assertTrue(isinstance(mni.get_nodes()[0], node.Node))
        self.assertTrue(isinstance(mni.get_nodes()[0], node.QuantoTestbedMote))

        os.remove(fileName)


    def test_compilation(self):
        fileName = "config.ini"
        f = file(fileName, 'w')
        confString = """
[Nodes]
numNodes: 1
type: QuantoTestbedMote
makeCmd: ls

[Node1]
id: 1
ip: 172.17.6.102
serial: /dev/ttyrb00
installCmd: make epic miniprog reinstall,1 bsl,/dev/ttyrb00
"""
        f.write(confString)
        f.close()

        mni = MNI()

        self.assertTrue(mni.compile())

        f = file(fileName, 'w')
        confString = """
[Nodes]
numNodes: 1
type: QuantoTestbedMote
makeCmd: make nothingtomake

[Node1]
id: 1
ip: 172.17.6.102
serial: /dev/ttyrb00
installCmd: make epic miniprog reinstall,1 bsl,/dev/ttyrb00
"""
        f.write(confString)
        f.close()

        mni = MNI()

        self.assertFalse(mni.compile())


        os.remove(fileName)


    def test_install_all(self):
        fileName = "config.ini"
        f = file(fileName, 'w')
        confString = """
[Nodes]
numNodes: 2
type: QuantoTestbedMote
makeCmd: ls

[Node1]
id: 1
ip: 172.17.6.102
serial: /dev/ttyrb00
installCmd: make epic miniprog reinstall,1 bsl,/dev/ttyrb00

[Node2]
id: 2
ip: 172.17.6.103
serial: /dev/ttyrc00
installCmd: make epic miniprog reinstall,1 bsl,/dev/ttyrc00
"""
        f.write(confString)
        f.close()

        mni = MNI()

        self.assertTrue(mni.compile())
        self.assertFalse(mni.install_all())



if __name__ == "__main__":
    unittest.main()
