from mni import *
import numpy

try:
    import cvxmod
    from cvxmod.atoms import norm2
    cvxAvailable = True
except:
    cvxAvailable = False

class QuantoMNI(MNI):

    def __init__(self, configFile="config.ini"):
        """Initialize a managed quanto node infrastructure.

        We will first check for quanto specific paremeters, before we call MNI
        itself for the rest of the work.
        """

        if "TOSROOT" not in os.environ.keys():
            sys.stderr.write("""
ERROR: the Quanto Environment is not setup!
Please run quanto_setup.sh before creating a QuantoMNI object.
""")
            sys.exit(1)

        MNI.__init__(self, configFile)

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

    def stop_all(self):
        processes = []
        for n in self.nodes:
            p = threading.Thread(target=n.stop)
            p.start()
            processes.append(p)

        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if p.isAlive():
                    runningProcesses.append(p)

            processes = runningProcesses
            time.sleep(0.1)


    def press_usr_all(self):
        processes = []
        for n in self.nodes:
            p = threading.Thread(target=n.push_usr)
            p.start()
            processes.append(p)

        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if p.isAlive():
                    runningProcesses.append(p)

            processes = runningProcesses
            time.sleep(0.1)
        for n in self.nodes:
            p = threading.Thread(target=n.release_usr)
            p.start()
            processes.append(p)

        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if p.isAlive():
                    runningProcesses.append(p)

            processes = runningProcesses
            time.sleep(0.1)

    def calibrate_all(self, doInstallCompile=True, readFromFile=False,
            configFile='calibration.ini'):
        currentDir = os.getcwd()
        os.chdir(os.path.join(os.environ['TOSROOT'],"apps/quantoApps/CalibrateQuanto"))
        # add the current path so that the next import of calibratequanto
        # works
        sys.path.insert(0, os.getcwd())
        import calibratequanto

        if readFromFile:
            # read the calibration data from file
            config = ConfigParser.RawConfigParser()
            config.read(configFile)

            for n in self.nodes:
                if not config.has_option("Node%s"%(n.ip), 'calibration'):
                    raise ConfigParser.NoOptionError("Node%s"%(n.ip),
                            'calibration')
                calibration = config.get("Node%s"%(n.ip,), 'calibration')
                # FIXME: DANGEROUS!!! Prone to code injection!
                # FIXME: We should write our own parser for dictionaries.
                # ensure that eval can not use any builtin functions
                globs = {'__buildins__':{}}
                n.calibrate(eval(calibration, globs, globs))

        else:
            # compile and install calibration application, connect to the
            # nodes to get the calibration

            if doInstallCompile:
                try:
                    self.compile()
                except CompileError, e:
                    raise CompileError, e
                try:
                    self.install_all()
                except InstallError, e:
                    raise InstallError, e

            # run calibration
            processes = []
            calibrations = []
            for n in self.nodes:
                cq = calibratequanto.CalibrateQuanto(
                        serial="serial@%s:epic"%n.serial,
                        repeat=False,
                        debug=False)
                p = threading.Thread(target=cq.listen)
                p.start()
                processes.append(p)
                calibrations.append((n, cq))

            while len(processes) > 0:
                runningProcesses = []
                for p in processes:
                    if p.isAlive():
                        runningProcesses.append(p)

                processes = runningProcesses
                time.sleep(0.1)

            # we got the data from the actual motes. Safe it in a
            # configuration file so that we can reread it later
            config = ConfigParser.RawConfigParser()

            for (n, cq) in calibrations:
                n.calibrate(cq.frequencies)
                # write this node's configuration
                config.add_section("Node%s"%(n.ip,))
                config.set("Node%s"%(n.ip,), "calibration",
                        str(cq.frequencies))
                config.set("Node%s"%(n.ip,), "calibrationDate",
                        time.ctime())

            # write the configuration file
            config.write(open(configFile, 'wb'))

        # go back to the old directory
        os.chdir(currentDir)

    def parse_quanto_log_all(self, baseFileName):
        """Decompress, then parse the quanto message logfile using the "read_log.py"
        application. This will generate a .parsed and a .pwr file for each
        node."""

        allProcesses = []

        #for n in self.nodes:
        #    cmd = "quanto_decode"
        #    p = msp.ManagedSubproc(cmd,
        #            stderr_fid=StringIO.StringIO(),
        #            stdout_fid=file("%s.%s.log"%(baseFileName, n.ip), "w"),
        #            stdin_fid=file("%s.%s.cmp"%(baseFileName, n.ip)))
        #    p.start()
        #    allProcesses.append(p)

        processes = allProcesses
        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if not p.is_dead():
                    runningProcesses.append(p)
            processes = runningProcesses
            time.sleep(0.1)
            for p in processes:
                print "".join(p.stderr_fid.getvalue())


        allProcesses = []
        for n in self.nodes:
            p = msp.ManagedSubproc(
                    "read_log.py %s.%s.log %d"%(baseFileName, n.ip, n.timeoffset),
                    stderr_fid=StringIO.StringIO(),
                    stdout_fid=StringIO.StringIO())
            p.start()
            allProcesses.append(p)

        processes = allProcesses
        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if not p.is_dead():
                    runningProcesses.append(p)
            processes = runningProcesses
            time.sleep(0.1)

        for p in allProcesses:
                if p.returncode() != 0:
                    raise ParseError, "\
ERROR while executing '%s'\
Output from read_log.py:\
%s\n%s"%(" ".join(p.command_line), "".join(p.stdout_fid.getvalue()), "".join(p.stderr_fid.getvalue()))

    def process_quanto_log_all(self, baseFileName):
        """Processes the parsed quanto message file using the "process.pl"
        application. This will generate a .parsed.eps, .parsed.gp, and
        .parsed.times file for each node."""

        allProcesses = []
        for n in self.nodes:
            p = msp.ManagedSubproc(
                    "process.pl -f %s.%s.log.parsed"%(baseFileName, n.ip),
                    stderr_fid=StringIO.StringIO(),
                    stdout_fid=StringIO.StringIO())
            p.start()
            allProcesses.append(p)

        processes = allProcesses
        while len(processes) > 0:
            runningProcesses = []
            for p in processes:
                if not p.is_dead():
                    runningProcesses.append(p)
            processes = runningProcesses
            time.sleep(0.1)

        for p in allProcesses:
                if p.returncode() != 0:
                    raise ParseError, "\
ERROR while executing '%s'\
Output from process.pl:\
%s\n%s"%(" ".join(p.command_line), "".join(p.stdout_fid.getvalue()), "".join(p.stderr_fid.getvalue()))


    def get_energy_per_quanto_state_all(self, baseFileName, convexOpt=False):
        """This function evaluates the .pwr file and calculates the individual
        power consumption per state for every node. It then sets the variable
        statePower on every node to a dictionary, where the keys are the
        string representation of the state, and the value is the average power
        consumption for that state.

        This function expects a very specific .pwr file, where one line starts
        with "#states:". This line encodes all the states that are considered
        by quanto.
        """

        for n in self.nodes:
            f = open("%s.%s.log.pwr"%(baseFileName, n.ip), "r")
            X = []
            Y = []
            W = []
            totalTime = 0
            totalEnergy = 0
            states = []
            maxEntries = 0
            for line in f:
                l = line.strip().split()
                if len(l) > 0 and l[0] == "#states:":
                        # this line encodes the names of all the states.
                        states = l[1:]
                        continue
                if len(states) == 0 or len(l) != len(states)+3:
                    # +2 comes from the icount and time field
                    continue
                #time is in uS, convert it to seconds
                time = float(l[-3])/1e6
                icount = int(l[-2])
                occurences = int(l[-1])
                # cut away the time and icount values
                l = l[0:-3]
                activeStates = []
                for s in l:
                    if s == '-':
                        s = '0'
                        #continue
                    activeStates.append(int(s))

                # add the constant power state
                activeStates.append(1)

                if len(activeStates) > maxEntries:
                    maxEntries = len(activeStates)

                if time <= 0 or icount <= 0:
                    # FIXME: this is a wrong line at the end of the quanto files. I
                    # don't know why this happens!!!
                    continue

                E = n.get_power(icount, time)
                if E == -1:
                    raise CalibrationError, "Node with IP %s is not calibrated! \
Did you forget to load the calibration file?"%(n.ip,)
                if E < 0:
                    raise CalibrationError, "Node with IP %s returned a \
negative Energy value %f for icount %d, time %f!"%(n.ip, E, icount, time)
                    continue
                X.append(activeStates)
                Y.append(E)
                W.append(numpy.sqrt(E*time))
                totalTime += time
                totalEnergy += E*time



            # filter out the incomplete datasets
            Xnew = []
            Ynew = []
            Wnew = []
            for i in range(len(Y)):
                if len(X[i]) == maxEntries:
                    Xnew.append(X[i])
                    Ynew.append(Y[i])
                    Wnew.append(W[i])
            X = numpy.matrix(Xnew)
            Y = numpy.matrix(Ynew)
            W = numpy.matrix(numpy.diag(Wnew))

            # filter states with all 0's
            states.append('const')
            deletedLines = 0
            deletedStates = []
            alwaysOnStates = []
            # iterate through all the states, except the 'const' state
            for i in range(len(states)-1):
                correctedI = i - deletedLines
                if numpy.sum(X.T[correctedI]) == 0:
                    deletedStates.append(states[correctedI])
                    X = numpy.delete(X, numpy.s_[correctedI:correctedI+1], axis=1)
                    states = numpy.delete(states, correctedI)
                    deletedLines += 1
                elif numpy.sum(X.T[correctedI]) == len(X):
                    # this state is always active. W have to remove them and
                    # put them into the "const" category!
                    alwaysOnStates.append(states[correctedI])
                    X = numpy.delete(X, numpy.s_[correctedI:correctedI+1], axis=1)
                    states = numpy.delete(states, correctedI)
                    deletedLines += 1

            # search for linear dependent lines
            #for i in range(len(X)):
            #    #print X[i]
            #    for j in range(i+1, len(X)):
            #        #if numpy.sum(X[i]) == numpy.sum(X[j]):
            #        #    print X[i], X[j]
            #        equal = True
            #        for m in range(X[i].shape[1]):
            #            if X[i,m] != X[j,m]:
            #                equal = False
            #                break

            #        if equal:
            #            print X[i], X[j]

            # maxEntries includes the const state, which is not in the states
            # variable yet
            #states = states[:maxEntries - 1]

            #xtwx = X.T*X
            #for i in range(len(xtwx)):
            #    print xtwx[i]
            #print states

            #(x, resids, rank, s) = numpy.linalg.lstsq(W*X, W*Y.T)
            #(x, resids, rank, s) = numpy.linalg.lstsq(X, Y.T)

            if cvxAvailable and convexOpt:

                A = cvxmod.matrix(W*X)
                b = cvxmod.matrix(W*Y.T)
                x = cvxmod.optvar('x', cvxmod.size(A)[1])

                print A
                print b

                p = cvxmod.problem(cvxmod.minimize(norm2(A*x - b)), [x >= 0])
                #p.constr.append(x |In| probsimp(5))
                p.solve()

                print "Optimal problem value is %.4f." % p.value
                cvxmod.printval(x)
                x = x.value

            else:

                try:
                    x = numpy.linalg.inv(X.T*W*X)*X.T*W*Y.T
                except numpy.linalg.LinAlgError, e:
                    sys.stderr.write("State Matrix X for node with IP %s is singular. We did not \
    collect enough energy and state information. Please run the application for \
    longer!\n"%(n.ip,))
                    sys.stderr.write(repr(e))
                    sys.stderr.write("\n")
                    sys.stderr.flush()
                    n.statePower = {}
                    n.alwaysOffStates = []
                    n.alwaysOnStates = []
                    continue
            n.statePower = {}
            for i in range(len(states)):
                # the entries in x are matrices. convert them back into a
                # number
                n.statePower[states[i]] = float(x[i])
            n.alwaysOffStates = deletedStates
            n.alwaysOnStates = alwaysOnStates
            n.averagePower = totalEnergy / totalTime
