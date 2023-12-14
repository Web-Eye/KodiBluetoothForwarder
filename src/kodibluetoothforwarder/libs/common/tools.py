# -*- coding: utf-8 -*-
# Copyright 2023 WebEye
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import evdev
import socket
import ipaddress
from evdev import ecodes


def getBluetoothController(mac):
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device.phys == mac:
            return device

    return None


def eventCodeToString(event):
    codes = ecodes.KEY[event.code]
    t = type(codes)
    if t is str:
        return codes
    elif t is list:
        return codes[0]

    return None


def eventValueToString(event):
    return ('RELEASE', 'PRESS', 'HOLD')[event.value]


def getKeyFlag(key):

    if key in ('KEY_LEFTCTRL', 'KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT', 'KEY_LEFTALT', 'KEY_RIGHTALT', 'KEY_RIGHTCTRL',
               'KEY_LEFTMETA', 'KEY_RIGHTMETA'):
        return {
            'KEY_LEFTCTRL':   0x01,
            'KEY_LEFTSHIFT':  0x02,
            'KEY_RIGHTSHIFT': 0x04,
            'KEY_LEFTALT':    0x08,
            'KEY_RIGHTALT':   0x10,
            'KEY_RIGHTCTRL':  0x20,
            'KEY_LEFTMETA':   0x40,
            'KEY_RIGHTMETA':  0x80
        }[key]

    return 0


def getEventData(event):
    key = eventCodeToString(event)
    flag = getKeyFlag(key)
    eValue = eventValueToString(event)
    return key, flag, eValue


def create_magic_packet(macaddress: str) -> bytes:
    if len(macaddress) == 17:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, "")
    elif len(macaddress) == 14:
        sep = macaddress[4]
        macaddress = macaddress.replace(sep, "")
    if len(macaddress) != 12:
        raise ValueError("Incorrect MAC address format")
    return bytes.fromhex("F" * 12 + macaddress * 16)


def _is_ipv6_address(ip_address: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(ip_address), ipaddress.IPv6Address)
    except ValueError:
        return False


def sendWOLPackage(mac):
    BROADCAST_IP = "255.255.255.255"
    DEFAULT_PORT = 9

    if mac:
        try:
            ip_address = BROADCAST_IP
            port = DEFAULT_PORT
            packet = create_magic_packet(mac)
            address_family = (
                socket.AF_INET6 if _is_ipv6_address(ip_address) else socket.AF_INET
            )
            with socket.socket(address_family, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.connect((ip_address, port))
                sock.send(packet)

        finally:
            pass
