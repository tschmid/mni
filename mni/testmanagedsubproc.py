import managedsubproc
import tempfile
import unittest
import time
import os

# Helper function maintained outside of the test suite.  Used to
# demonstrate how external functions can be registered to handle output
# from a managed subprocess.
count_on_test = 0
def is_test(s):
    global count_on_test
    if s == "test\n":
        count_on_test += 1

class TestManagedSubproc(unittest.TestCase):

    def test_object_creation(self):
        m = managedsubproc.ManagedSubproc("echo test")
        self.assertEqual(m.command_line, ["echo", "test"])
        self.assertEqual(m.stdout_disk, None)
        self.assertEqual(m.stdout_fid, None)
        self.assertEqual(m.stdout_fns, [])
        self.assertEqual(m.stderr_disk, None)
        self.assertEqual(m.stderr_fid, None)
        self.assertEqual(m.stderr_fns, [])
        self.assertEqual(m.has_started, False)

    def test_start(self):
        m = managedsubproc.ManagedSubproc("echo test")
        m.start()
        self.assertEqual(m.has_started, True)

    def test_double_start(self):
        m = managedsubproc.ManagedSubproc("echo test")
        m.start()
        self.assertRaises(AssertionError, m.start)

    def test_start_stop(self):
        m = managedsubproc.ManagedSubproc("echo test")
        m.start()
        self.assertFalse(m.is_dead())
        m.stop()
        self.assertTrue(m.is_dead())

    def test_stop_streams(self):
        m = managedsubproc.ManagedSubproc("echo test")
        self.assertEquals(m.stdout_manager, None)
        self.assertEquals(m.stderr_manager, None)
        m.start()
        self.assertNotEquals(m.stdout_manager, None)
        self.assertNotEquals(m.stderr_manager, None)
        m.stop()
        self.assertEquals(m.stdout_manager, None)
        self.assertEquals(m.stderr_manager, None)


    def test_stdout_disk(self):
        disk_name = tempfile.mktemp()
        m = managedsubproc.ManagedSubproc("echo test",
                stdout_disk=disk_name)
        m.start()
        while not m.is_dead():
            time.sleep(0.1)
        m.stop()
        out_disk = open(disk_name, "r")
        self.assertEqual(out_disk.readline(), "test\n")
        os.remove(disk_name)


    def test_stdout_file(self):
        file_name = tempfile.mktemp()
        f = open(file_name, "w")
        m = managedsubproc.ManagedSubproc("echo test",
                stdout_fid=f)
        m.start()
        while not m.is_dead():
            time.sleep(0.1)
        m.stop()
        out_file = open(file_name, "r")
        self.assertEqual(out_file.readline(), "test\n")
        out_file.close()
        os.remove(file_name)

    def test_stdout_disk_file(self):
        disk_name = tempfile.mktemp()
        file_name = tempfile.mktemp()
        f = open(file_name, "w")
        # With the - option, tee will write data from stdin to stdout
        # twice.  See man tee for more details.
        m = managedsubproc.ManagedSubproc("tee -",
                stdout_disk=disk_name, stdout_fid=f)
        m.start()
        m.write("test\n")
        time.sleep(0.1)
        m.stop()
        out_disk = open(file_name, "r")
        self.assertEqual(out_disk.readline(), "test\n")
        self.assertEqual(out_disk.readline(), "test\n")
        out_disk.close()
        os.remove(disk_name)
        out_file = open(file_name, "r")
        self.assertEqual(out_file.readline(), "test\n")
        self.assertEqual(out_file.readline(), "test\n")
        out_file.close()
        os.remove(file_name)

    def test_stdout_functions(self):

        m = managedsubproc.ManagedSubproc("echo test",
                stdout_fns=[is_test, is_test])
        m.start()
        while not m.is_dead():
            time.sleep(0.1)
        m.stop()
        self.assertEqual(count_on_test, 2)

if __name__ == '__main__':
    unittest.main()
