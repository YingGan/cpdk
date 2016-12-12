import os
import sys
import time
import signal
import pexpect
import subprocess
from unittest import TestCase


class RedShellTest(TestCase):

    cpdkd_process = None

    def setUp(self):

        # Generate RedShell schema
        pexpect.run('python cpdk-util.py --settings examples.basic.settings --syncdb')
        pexpect.run('python cpdk-util.py --settings examples.basic.settings --buildcli')

        # Start CPDKd
        self.cpdkd_process = subprocess.Popen('python CPDKd.py --settings examples.basic.settings',
                                              stdout=subprocess.PIPE,
                                              shell=True, preexec_fn=os.setsid)

        # Wait for CPDKd to get started up
        time.sleep(3)
        self.assertIsNone(self.cpdkd_process.poll())

    def tearDown(self):
        # Stop CPDKd
        os.killpg(os.getpgid(self.cpdkd_process.pid), signal.SIGTERM)

    def test_virtual_server(self):
        """
        Verfiy that all of the virtual server model operations are present and function
        """
        c = pexpect.spawn('python redshell.py --settings examples.basic.settings')
        c.logfile = sys.stdout
        c.expect('Global>')
        c.sendline('virtual Vippy')
        c.expect('virtual-Vippy>')

        # Validate setting the enabled flag works, and shows up in the show screen
        c.sendline('enabled')
        c.expect('virtual-Vippy>')
        c.sendline('show virtual Vippy')
        c.expect('virtual-Vippy>')
        self.assertIn('Enabled: True', c.before)

        # Invert the enabled flag (aka disable) and finish configuring the item
        c.sendline('disabled')
        c.expect('virtual-Vippy>')
        c.sendline('port 1234')
        c.expect('virtual-Vippy>')
        c.sendline('address 1.1.1.1')
        c.expect('virtual-Vippy>')
        c.sendline('exit')
        c.expect('Global>')
        c.sendline('show virtual Vippy')
        c.expect('Global>')

        # Make sure the appropriate fields are present
        self.assertIn('Address: 1.1.1.1', c.before)
        self.assertIn('Port: 1234', c.before)
        self.assertIn('Enabled: False', c.before)
        self.assertIn('Virtual Server: Vippy', c.before)
        c.sendline('exit')
        c.close()




