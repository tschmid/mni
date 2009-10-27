import unittest

from node import *

class TestNode(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_required_attributes(self):
        self.assertTrue("id" in Node.get_required_attributes())

    def test_configure(self):
        # check first parameter
        n = Node()

        configuration = {"id" : "string"}
        self.assertRaises(ValueError, n.configure, configuration)

    def test_install(self):
        n = Node()

        configuration = {"id" : "string"}
        n.install()
        self.assertTrue(n.is_install_success())


class TestQuantoTestbedMote(unittest.TestCase):
    """Unit test module for the Quanto Testbed Mote. Note that the
    configuration in the <code>setUp</code> method has to be for a real Quanto
    Testbed Mote, such that it can test install etc"""

    def setUp(self):
        self.realConfig = {"id": 1, "ip": "172.17.6.102", "serial":
                "/dev/ttyrb00", "installCmd": "ls"}

    def tearDown(self):
        pass

    def test_required_attributes(self):
        self.assertTrue("id" in QuantoTestbedMote.get_required_attributes())
        self.assertTrue("ip" in QuantoTestbedMote.get_required_attributes())
        self.assertTrue("serial" in
                QuantoTestbedMote.get_required_attributes())
        self.assertTrue("installCmd" in
                QuantoTestbedMote.get_required_attributes())

    def test_configure(self):
        n = QuantoTestbedMote()

        # check IP
        configuration = {"id" : 1, "ip": "0.0.0.0", "serial":
                "/dev/nosuchthing", "installCmd": "ls"}
        self.assertRaises(ValueError, n.configure, configuration)

        # check serial port
        configuration = {"id" : 1, "ip": "172.17.6.102", "serial":
                "/dev/nosuchthing", "installCmd": "ls"}
        self.assertRaises(ValueError, n.configure, configuration)

        # check install cmd
        configuration = {"id" : 1, "ip": "172.17.6.102", "serial":
                "/dev/ttyS0" }
        self.assertRaises(KeyError, n.configure, configuration)



    def test_install(self):
        n = QuantoTestbedMote()

        n.configure(self.realConfig)
        n.install()
        self.assertTrue(n.is_install_success())


if __name__ == "__main__":

    unittest.main()
