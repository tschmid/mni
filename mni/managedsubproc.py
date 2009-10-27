#!/usr/bin/python

# Author: Roy Shea
# Date: 2008, 2009

import subprocess
import signal
import os
import time
import sys
import threading


class ManagedSubproc:
    """Utility to create, command, and manage input and output of a subprocess."""

    def __init__(self, command_line,
            stdout_disk=None, stdout_fid=None, stdout_fns=[],
            stderr_disk=None, stderr_fid=None, stderr_fns=[],
            stdin_fid=None):
        """Prepare a subprocess.  After creation the subprocess is
        started by executing the object's start function.  Execution is
        stoped by executing the object's stop function.

        command_line:
                Command line used to start the proccess (require)

        stdout_disk:
                Name of a file to create and write stdout to.

        stdout_fid:
                File ID to write stdout to.

        stdout_fns:
                Each function in this list is called for each line
                of stdout.

        stderr_disk:
                Name of a file to create and write stderr to.

        stderr_fid:
                File ID to write stderr to.

        stderr_fns:
                Each function in this list is called for each line
                of stderr.
        """

        self.command_line = command_line.split()
        self.stdout_disk = stdout_disk
        self.stdout_fid = stdout_fid
        self.stdout_fns = stdout_fns
        self.stdin_fid = stdin_fid
        self.stderr_disk = stderr_disk
        self.stderr_fid = stderr_fid
        self.stderr_fns = stderr_fns
        self.stdout_manager = None
        self.stderr_manager = None
        self.has_started = False


    def start(self):
        """Execute the child process."""
        assert (not self.has_started)

        if(not self.stdin_fid):
            self.stdin_fid = subprocess.PIPE

        self.child = subprocess.Popen(self.command_line, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=self.stdin_fid)

        # Start thread to manage stdout
        stdout_manager = threading.Thread(target=self._manage_output,
                args=[self.child.stdout])
        stdout_manager.start()
        self.stdout_manager = stdout_manager

        # Start thread to manage stdout
        stderr_manager = threading.Thread(target=self._manage_output,
                args=[self.child.stderr])
        stderr_manager.start()
        self.stderr_manager = stderr_manager

        self.has_started = True


    def stop(self):
        """Stop the child process."""
        assert (self.has_started)

        # Stop the child processes
        self._stop_child_process()

        # Gather the output threads
        self.stdout_manager.join()
        self.stdout_manager = None
        self.stderr_manager.join()
        self.stderr_manager = None

        self.has_started = False


    def write(self, str):
        """Write string to stdin of the child process."""
        assert (self.has_started)
        self.child.stdin.write(str)


    def is_dead(self):
        """Checks if managed process is dead."""

        # Poll is catches cases where process is currently in a defunct
        # state.
        if self.child.poll() != None:
            return True

        # TODO: Is this needed in addition to the poll?
        try:
            return (os.kill(self.child.pid, 0) != None)
        except OSError, e:
            #process is dead
            if e.errno == 3: return True
            #no permissions
            elif e.errno == 1: return False
            else: raise

    def returncode(self):
        """Return the exit value, or None if the process is not dead yet."""
        return self.child.returncode


    def _manage_output(self, stream):
        """Write input from stream to disk and fid."""

        # Test if this is for stdout or stderr and setup outputs
        # appropriatly.
        disk_file = None
        fid = None
        if stream == self.child.stdout:
            if self.stdout_disk:
                disk_file = open(self.stdout_disk, "w")
            if self.stdout_fid:
                fid = self.stdout_fid
            fns = self.stdout_fns
        elif stream == self.child.stderr:
            if self.stderr_disk:
                disk_file = open(self.stderr_disk, "w")
            if self.stderr_fid:
                fid = self.stderr_fid
            fns = self.stderr_fns
        else:
            assert False, "Unexpected Stream"

        # Read lines while the stream is open
        for line in stream:
            if disk_file:
                disk_file.write(line)
                disk_file.flush()
            if fid:
                fid.write(line)
                fid.flush()
            for fn in fns:
                fn(line)

        # Clean up if neccessary
        if disk_file:
            disk_file.close()


    def _stop_child_process(self):
        """Uses signals of escalating severity to kill PID."""

        if self.is_dead(): return

        for sig in [signal.SIGUSR1, signal.SIGTERM, signal.SIGINT,
                signal.SIGHUP, signal.SIGKILL]:
            os.kill(self.child.pid, sig)
            if self.is_dead(): break
        self.child.wait()
        return


if __name__ == "__main__":
    assert False, "Not an executable script"


