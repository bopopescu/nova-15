__author__ = 'root'

from nova.openstack.common import log as logging
from oslo.config import cfg
from nova import exception
import socket
import os
import json

import threading
import time

LOG = logging.getLogger(__name__)

ovirtguestagent_opts = [
    cfg.BoolOpt('enable_set_admin_password',
                default=True,
                help='Enable kvm set_admin_password by oga'),
    cfg.BoolOpt('enable_rename',
                default=True,
                help='Enable kvm rename by oga'),
    ]

CONF = cfg.CONF
CONF.register_opts(ovirtguestagent_opts)
CONF.import_opt('virt_type', 'nova.virt.libvirt.driver', group='libvirt')


_VMCHANNEL_DEVICE_NAME = 'com.redhat.rhevm.vdsm'
_PREFIX = "/var/lib/libvirt/qemu/"
_TRY_TIMES = 3
_TIMEOUT = 10


class OvirtGA():
    def __init__(self):
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.settimeout(10)

    def rename(self, hostname, instance_name):
        if hostname == "" or hostname is None:
            raise exception.NovaException("called rename but hostname is empty")

        if CONF.enable_rename and CONF.libvirt.enable_ovirt_ga:
            sock_path = _PREFIX + _VMCHANNEL_DEVICE_NAME + "." + instance_name + ".sock"
            if os.path.exists(sock_path):
                try:
                    self._connect(sock_path)
                except socket.timeout as e:
                    LOG.error("connected to ovirtga timeout, It seems ovirt guest agent is down, So rename failed")
                    raise socket.timeout("connected to ovirtga timeout, It seems ovirt guest agent is down, So rename failed")
                except socket.error as e:
                    LOG.error("connected to ovirtga failed, %s", e.message)
                    raise exception.SetAdminPasswordFailed("connected to ovirtga failed" + e.message)
                try:
                    self._forward("rename", {'hostname':hostname})
                except socket.timeout as e:
                    LOG.error("send rename command to ovirtga timeout")
                    raise socket.timeout("send rename command to ovirtga timeout")
                try:
                    (name, args) = self._recv_status()
                except socket.timeout as e:
                    LOG.error("recv rename return status timeout")
                    raise socket.timeout("recv rename return status timeout")
                if name != "rename_result":
                    LOG.error("ovirt guest agent return keyword error, it should not happen")
                    raise exception.NovaException("ovirt guest agent return keyword error, it should not happen")
                else:
                    if args["ret"] != 0:
                        LOG.error("rename failed, ret = %d", args["ret"])
                        raise exception.NovaException("ovirt guest agent exec rename failed, ret =" + str(args["ret"]))
                    else:
                        LOG.info("rename OK")
            else:
                LOG.error("Instance %s socket file %s does not exist!", instance_name, sock_path)
                raise exception.NovaException("ovirt-guest-agent channel file is not exist path = " + sock_path)
        else:
            LOG.warn("rename is not enable in config file")
            raise NotImplementedError()


    def set_admin_password(self, password, instance_name):
        if password == "" or password is None:
            raise exception.SetAdminPasswordFailed("called set_admin_password but password is empty")

        if CONF.enable_set_admin_password and CONF.libvirt.enable_ovirt_ga:
            sock_path = _PREFIX + _VMCHANNEL_DEVICE_NAME + "." + instance_name + ".sock"
            if os.path.exists(sock_path):
                try:
                    self._connect(sock_path)
                except socket.timeout as e:
                    LOG.error("connected to ovirtga timeout, It seems ovirt guest agent is down, So set_admin_password failed")
                    raise socket.timeout("connected to ovirtga timeout, It seems ovirt guest agent is down, So set_admin_password failed")
                except socket.error as e:
                    LOG.error("connected to ovirtga failed, %s", e.message)
                    raise exception.SetAdminPasswordFailed("connected to ovirtga failed" + e.message)
                try:
                    self._forward("set_admin_password", {'admin_password':password})
                except socket.timeout as e:
                    LOG.error("send set_admin_password command to ovirtga timeout")
                    raise socket.timeout("send set_admin_password command to ovirtga timeout")
                try:
                    (name, args) = self._recv_status()
                except socket.timeout as e:
                    LOG.error("recv set_admin_password return status timeout")
                    raise socket.timeout("recv set_admin_password return status timeout")
                if name != "set_admin_password_result":
                    LOG.error("ovirt guest agent return keyword error, it should not happen")
                    raise exception.SetAdminPasswordFailed("ovirt guest agent return keyword error, it should not happen")
                else:
                    if args["ret"] != 0:
                        LOG.error("set_admin_password failed, ret = %d", args["ret"])
                        raise exception.SetAdminPasswordFailed("ovirt-guest-agent exec set_admin_password failed, ret = " + str(args["ret"]))
                    else:
                        LOG.info("set_admin_password OK")
            else:
                LOG.error("Instance %s socket file %s does not exist!", instance_name, sock_path)
                raise exception.SetAdminPasswordFailed("ovirt-guest-agent channel file is not exist path = " + sock_path)
        else:
            LOG.warn("set_admin_password is not enable in config file")
            raise NotImplementedError()

    def _forward(self, cmd, args={}):
        args['__name__'] = cmd
        message = (json.dumps(args) + '\n').encode('utf8')
        self._sock.send(message)
        LOG.debug('sent %s', message)

    def _connect(self, sock_path):
        LOG.debug("ovirt-guest-agent path = %s", sock_path)
        self._sock.connect(sock_path)
        self._forward("bcec")
        (name, args) = self._recv_status()
        if name != "bcec":
            LOG.error("ovirt guest agent init handshake error")
            raise exception.NovaException("ovirt guest agent init handshark error")

    def _recv_status(self):
        data = self._sock.recv(1024)
        (name, args) = self._parseLine(data)
        return (name, args)

    def _parseLine(self, line):
        try:
            args = json.loads(line.decode('utf8'))
            name = args['__name__']
            del args['__name__']
        except:
            name = None
            args = None
        return (name, args)

    def close(self):
        self._sock.close()


def test_oga(sock_path, instance_name, password):
    time.sleep(5)
    oga = OvirtGA()
    try:
        oga.set_admin_password(password, instance_name)
    except BaseException as e:
        LOG.error("come here %s", e.message)
        raise exception.SetAdminPasswordFailed(reason=e.message)
    finally:
        oga.close()

if __name__ == "__main__":
    _VMCHANNEL_DEVICE_NAME = "/1qaz2wsx"
    _PREFIX = "/tmp"
    instance = "instance-0000007"
    sock_path = _PREFIX + _VMCHANNEL_DEVICE_NAME + "." + instance + ".sock"
    t = threading.Thread(target=test_oga, args=(sock_path, instance,"Abcd1234"))
    t.start()
    client = OvirtGA()
    args = {}

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    sock.bind(sock_path)
    sock.listen(5)

    con,addr = sock.accept()
    print "main"
    data = con.recv(1024)
    print data
    #(name, args) = client._parseLine(data)
    args['__name__'] = "bcec"
    message = (json.dumps(args) + '\n').encode('utf8')
    con.send(message)
    data = con.recv(1024)
    print data
    args2 = {'ret':0}
    args2['__name__'] = "set_admin_password_result"
    message = (json.dumps(args2) + '\n').encode('utf8')
    con.send(message)
    t.join()
    con.close()
    sock.close()
