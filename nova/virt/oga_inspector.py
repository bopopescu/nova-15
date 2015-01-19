#
# Copyright 2014  China Mobile Limited
#
# Author: Gangyi Luo <luogangyi@chinamobile.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from nova.openstack.common import log

import time
import os

from time import sleep
from ovirtga.guestagent import GuestAgent
from ovirtga.vmchannels import Listener
LOG = log.getLogger(__name__)

_VMCHANNEL_DEVICE_NAME = 'com.redhat.rhevm.vdsm'
# This device name is used as default both in the qemu-guest-agent
# service/daemon and in libvirtd (to be used with the quiesce flag).
_QEMU_GA_DEVICE_NAME = 'org.qemu.guest_agent.0'



class OGAInspector(object):

    def __init__(self):

        self.oga_dict = {}
        self.channelListener = Listener()

    def _get_agent(self, instance_name):
        guestSocketFile = self._make_channel_path(_VMCHANNEL_DEVICE_NAME, instance_name)
        if os.path.exists(guestSocketFile):
            guest_agent = GuestAgent(guestSocketFile, self.channelListener)
            self.channelListener.settimeout(30)
            self.channelListener.start()
            guest_agent.connect()
            self.oga_dict[instance_name] = guest_agent
            return guest_agent
        else:
            LOG.error("Instance %s socket file %s does not exist!" % (instance_name, guestSocketFile))
            return None

    def _make_channel_path(self, deviceName, instance_name):
        return "/var/lib/libvirt/qemu/%s.%s.sock" % (deviceName, instance_name)

    def mkdir(self, path, instance_name):
        guest_agent = self._get_agent(instance_name)
        print guest_agent.getGuestInfo()
        print guest_agent.guestDiskMapping
        print (guest_agent.isResponsive())
        if guest_agent and guest_agent.isResponsive():
            while(True):
                sleep(3)
                guest_agent.mkdir(path)
                guest_agent.isResponsive()
                print guest_agent.getGuestInfo()
        guest_agent.stop()

    def set_admin_password(self, admin_password, instance_name):
        guest_agent = self._get_agent(instance_name)
        print guest_agent.getGuestInfo()
        print guest_agent.guestDiskMapping
        print (guest_agent.isResponsive())
        if guest_agent and guest_agent.isResponsive():
            while(True):
                sleep(3)
                guest_agent.set_admin_password(admin_password)
                guest_agent.isResponsive()
                print guest_agent.getGuestInfo()
        guest_agent.stop()


if __name__ == '__main__':
    inspector = OGAInspector()
    inspector.set_admin_password("'''","instance-00000012")

