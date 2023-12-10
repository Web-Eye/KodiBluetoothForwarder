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
    return ('up', 'down', 'hold')[event.value]

