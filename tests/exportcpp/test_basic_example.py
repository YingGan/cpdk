import os
from subprocess import call
from unittest import TestCase


class BasicExample(TestCase):

    def test_exportcpp(self):
        """
        Validate cpdk-util.py successfully generates the required header files.
        """

        # Print out some debugging information about the environment
        call(['g++ -v'], shell=True)

        # Run cpdk-util and generate the C++ header files
        ret = call(['python', 'cpdk-util.py', '--settings', 'examples.basic.settings', '--exportcpp'])
        self.assertEqual(ret, 0)

        # Verify the generated files exist
        for f in ['./examples/basic/c_src/Interface.h',
                  './examples/basic/c_src/Server.h',
                  './examples/basic/c_src/VirtualServer.h']:
            self.assertTrue(os.path.exists(f))

        # Validate the example compiles
        ret = call(['cd ./examples/basic/c_src; make clean; make'], shell=True)
        self.assertEqual(ret, 0)

        # Clean up any files left around
        call(['cd ./examples/basic/c_src; make clean'], shell=True)
