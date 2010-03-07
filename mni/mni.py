import os
import sys
import ConfigParser
import node
import subprocess
import threading
import StringIO
import time
import managedsubproc as msp


class MNI:


    def __init__(self, configFile="config.ini"):
        """Initialize a managed node infrastructure.

        Initialization reads a configuration file to set testbed wide
        attributes such as number of nodes, the type of nodes in the
        testbed, and the make command specific to the node type.  The
        configuration also describes per-node details important for the
        testbed.
        """

        self.nodes = []
        self.nodeType = None
        self.serialProcesses = []

        # Parse configuration.
        self.configFileName = configFile
        try:
            self.config = ConfigParser.RawConfigParser()
            self.config.readfp(open(self.configFileName))
        except IOError:
            raise IOError(self.configFileName)

        # Verify presence of required testbed wide options specified in
        # the Nodes section.
        if not self.config.has_section("Nodes"):
            raise ConfigParser.NoSectionError("Nodes")
        self._verify_required_options("Nodes",
                ["numNodes", "type", "makeCmd"])

        # Set required testbed attributes.
        self.numNodes = self.config.getint("Nodes", "numNodes")
        self.type = self.config.get("Nodes", "type")
        self.makeCmd = self.config.get("Nodes", "makeCmd")

        # Load set of node specific required options.
        try:
            nodeType = getattr(node, self.type)
        except AttributeError:
            raise AttributeError, "Node Class %s does not exist!"%(self.type)
        attributes = nodeType.get_required_attributes()

        # Check that all nodes are defined in the configuration with all
        # the necessary attributes.
        for id in range(self.numNodes):
            # Use +1 because range starts at 0.
            nodeString = "Node"+str(id+1)

            # Verify presence of required options for current node.
            if not self.config.has_section(nodeString):
                raise ConfigParser.NoSectionError, "["+nodeString+"]"
            self._verify_required_options(nodeString, attributes)

            # Set required options for the current node.
            configuration = {}
            for a in attributes:
                configuration[a] = self.config.get(nodeString, a)

            self.nodes.append(nodeType())
            self.nodes[-1].configure(configuration)

    def reset_all(self):
        processes = []
        for n in self.nodes:
            p = threading.Thread(target=n.reset)
            p.start()
            processes.append(p)

        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if p.isAlive():
                    runningProcesses.append(p)

            processes = runningProcesses
            time.sleep(0.1)

    def _verify_required_options(self, section, options):
        """Verify that all options are included in section of self.config."""
        for option in options:
            if not self.config.has_option(section, option):
                raise ConfigParser.NoOptionError(option, section)


    def get_nodes(self):
        return self.nodes


    def compile(self):
        proc = subprocess.Popen(self.makeCmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        proc.wait()

        if proc.returncode != None:
            if proc.returncode == 0:
                return True
            else:
                # compilation failed
                sys.stderr.write(
"""ERROR: Compilation Failed. Output from command "%s":\n"""%(self.makeCmd,))
                sys.stderr.write("".join(proc.stdout.readlines()))
                sys.stderr.write("\n")
                sys.stderr.write("".join(proc.stderr.readlines()))
                raise CompileError, "Compilation with command '%s' failed."%(self.makeCmd)
                return False
        else:
            # something went wrong!
            raise CompileError, "Something went wrong while compiling!"
            return False


    def install_all(self):
        processes = []
        for n in self.nodes:
            p = threading.Thread(target=n.install)
            p.start()
            processes.append(p)

        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if p.isAlive():
                    runningProcesses.append(p)

            processes = runningProcesses
            time.sleep(0.1)

        # processes done. Collect exit codes
        installSuccess = True
        for n in self.nodes:
            if not n.is_install_success():
                installSuccess = False

        if not installSuccess:
            raise InstallError, "Installation Failed on at least 1 node!"
        return installSuccess

    def connect_serial_to_file_all(self, baseFileName, timeout=None,
            blocking=True):
        """This function will connect a serial forwarder to every node and log
        the output to a file of the form 'baseFileName.IPADDRESS.log'. An
        optional parameter timeout will stop the logging after a given time.
        Else, it will run forever, or until all subprocesses are dead (which
        shouldn't happen, except if the serial devices disappear, or an other
        error happens). If blocking is set to False, this function will return
        immediately and leave the connections to the serial ports running. A
        subsequent call to <code>disconnect_serial_to_file_all</code> will
        stop the processes that are still alive."""

        if len(self.serialProcesses) > 0:
            # there are still serial processes running. Stop them
            for n in self.serialProcesses:
                n.stop()
        self.serialProcesses = []
        for n in self.nodes:
            p = msp.ManagedSubproc(
                    "/usr/bin/java net.tinyos.tools.Listen -comm serial@%s:tmote"%(n.serial),
                    stdout_disk = baseFileName + ".%s.log"%(n.ip,),
                    stderr_disk = baseFileName + ".%s.stderr.log"%(n.ip,),
                    stdout_fns = [n.message_counter, ])
            p.start()
            self.serialProcesses.append(p)

        if not blocking:
            # we are done.
            return

        startTime = time.time()
        while len(self.serialProcesses) > 0:
            runningProcesses = []
            for p in self.serialProcesses:
                if not p.is_dead():
                    runningProcesses.append(p)
            self.serialProcesses = runningProcesses
            if (timeout != None) and (time.time() - startTime) > timeout:
                # timeout reached. Stop all the processes!
                for p in self.serialProcesses:
                    p.stop()
                break

            time.sleep(0.1)

    def disconnect_serial_to_file_all(self):
        """Method to stop all serial processes that are still running."""
        for n in self.serialProcesses:
            n.stop()
        self.serialProcesses = []



class CompileError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class InstallError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class CalibrationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value



if __name__ == "__main__":
    mni = MNI()
