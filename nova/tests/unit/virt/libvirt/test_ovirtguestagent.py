__author__ = 'root'

import socket
import os
import json

import threading
import time
from nova import test
from nova.virt.libvirt.ovirtguestagent import OvirtGA


class OvirtGATest(test.NoDBTestCase):
    ADMIN_PASSWORD = "Abcd1234"
    HOSTNAME = "hostname"

    def test_set_admin_password_client(self, instance_name, password):
        time.sleep(5)
        oga = OvirtGA()
        try:
            oga.set_admin_password(password, instance_name)
        except BaseException as e:
            print "errmsg = ",  e.message
        finally:
            oga.close()

    def test_rename_client(self, instance_name, hostname):
        time.sleep(5)
        oga = OvirtGA()
        try:
            oga.rename(hostname, instance_name)
        except BaseException as e:
            print "errmsg = ",  e.message
        finally:
            oga.close()

    def test_set_admin_password(self):
        _VMCHANNEL_DEVICE_NAME = 'com.redhat.rhevm.vdsm'
        _PREFIX = "/var/lib/libvirt/qemu/"
        instance_name = "instance-7"
        sock_path = _PREFIX + _VMCHANNEL_DEVICE_NAME + "." + instance_name + ".sock"
        args1 = {}

        t = threading.Thread(target=self.test_set_admin_password_client, args=(instance_name, self.ADMIN_PASSWORD))
        t.start()
        client = OvirtGA()

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(sock_path):
            os.unlink(sock_path)
        sock.bind(sock_path)
        sock.listen(5)

        con,addr = sock.accept()
        print "main"
        data = con.recv(1024)
        print data
        (name, args) = client._parseLine(data)
        self.assertEqual(name, "bcec")

        args1['__name__'] = "bcec"
        message = (json.dumps(args1) + '\n').encode('utf8')
        con.send(message)
        data = con.recv(1024)
        print data
        (name, args) = client._parseLine(data)
        self.assertEqual(name, "set_admin_password")
        self.assertEqual(args['admin_password'], self.ADMIN_PASSWORD)

        args2 = {'ret':0}
        args2['__name__'] = "set_admin_password_result"
        message = (json.dumps(args2) + '\n').encode('utf8')
        con.send(message)
        t.join()
        con.close()
        sock.close()

    def test_rename(self):
        _VMCHANNEL_DEVICE_NAME = 'com.redhat.rhevm.vdsm'
        _PREFIX = "/var/lib/libvirt/qemu/"
        instance_name = "instance-7"
        sock_path = _PREFIX + _VMCHANNEL_DEVICE_NAME + "." + instance_name + ".sock"
        args1 = {}

        t = threading.Thread(target=self.test_rename_client, args=(instance_name, self.HOSTNAME))
        t.start()
        client = OvirtGA()

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(sock_path):
            os.unlink(sock_path)
        sock.bind(sock_path)
        sock.listen(5)

        con,addr = sock.accept()
        data = con.recv(1024)
        print data
        (name, args) = client._parseLine(data)
        self.assertEqual(name, "bcec")

        args1['__name__'] = "bcec"
        message = (json.dumps(args1) + '\n').encode('utf8')
        con.send(message)
        data = con.recv(1024)
        print data
        (name, args) = client._parseLine(data)
        self.assertEqual(name, "rename")
        self.assertEqual(args['hostname'], self.HOSTNAME)

        args2 = {'ret':0}
        args2['__name__'] = "rename_result"
        message = (json.dumps(args2) + '\n').encode('utf8')
        con.send(message)
        t.join()
        con.close()
        sock.close()

if __name__ == "__main__":
    oga_test = OvirtGATest()
    oga_test.test_set_admin_password()
    oga_test.test_rename()
