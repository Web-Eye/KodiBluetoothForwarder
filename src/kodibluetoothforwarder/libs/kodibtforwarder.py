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
from socket import *


from .common.tools import *
from .core.xbmcclient import *

class KodiBTForwarder:

    def __init__(self):
        self._controller = '08:bf:b8:4a:5f:f6'
        self._xbmc_host = '192.168.2.113'
        self._xbmc_port = 9777
        self._mapping = 'HARMONY_WINDOWS'

    def start(self):

        xbmc = None

        try:
            while True:
                device = getBluetoothController(self._controller)
                if device is not None:
                    xbmc = XBMCClient(host=self._xbmc_host)
                    xbmc.connect()
                    xbmc.ping()
                while device is not None:
                    for event in device.read_loop():
                        if event.type == evdev.ecodes.EV_KEY:
                            # print(eventCodeToString(event))
                            # print(eventValueToString(event))
                            if event.value == 0:
                                xbmc.release_button()
                            elif event.value == 1:
                                xbmc.send_button(map='KB', button='up')




                time.sleep(0.5)

        except KeyboardInterrupt:
            pass

        if xbmc is not None:
            xbmc.close()





