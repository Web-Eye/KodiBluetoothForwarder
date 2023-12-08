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
import asyncio
from socket import *

from .common.tools import *
from .core.xbmcclient import *
from .core.rpcclient import *


async def wakeup_loop():
    while True:
        await asyncio.sleep(1)


class KodiBTForwarder:

    def __init__(self, config):
        self._config = config
        self._xbmc = None
        self._xbmc_connected = False
        self._controller = None

    async def ping_eventserver(self):
        while True:
            if self._xbmc_connected:
                self._xbmc.ping()

            await asyncio.sleep(50)

    async def monitorController(self):
        while True:
            if self._controller is None:
                self._controller = getBluetoothController(self._config['controller']['mac'])

            if self._controller is not None:
                try:
                    for event in self._controller.read_loop():
                        if event.type == evdev.ecodes.EV_KEY:
                            print(eventCodeToString(event))
                            print(eventValueToString(event))

                except error as e:
                    self._controller = None

            await asyncio.sleep(0.5)

    async def checkXBMC(self):
        host = self._config['XBMC']['host']
        rclient = rpcclient(host, self._config['XBMC']['webport'])
        while True:
            if not self._xbmc_connected:
                if rclient.ping():
                    self._xbmc = XBMCClient(host=host)

                # if available, start event client


            if  self._xbmc_connected:
                if not rclient.ping():
                    self._xbmc_connected = False

            if not self._xbmc_connected:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(120)

    def run(self):
        eventloop = asyncio.get_event_loop()
        eventloop.create_task(wakeup_loop())
        eventloop.create_task(self.monitorController())
        eventloop.create_task(self.checkXBMC())
        eventloop.create_task(self.ping_eventserver())

        try:
            eventloop.run_forever()
        except KeyboardInterrupt:
            pass


    # def run1(self):
    #
    #     xbmc = None
    #
    #     try:
    #         while True:
    #             device = getBluetoothController(self._controller)
    #             if device is not None:
    #                 xbmc = XBMCClient(host=self._xbmc_host)
    #                 xbmc.connect()
    #                 xbmc.ping()
    #             while device is not None:
    #                 for event in device.read_loop():
    #                     if event.type == evdev.ecodes.EV_KEY:
    #                         # print(eventCodeToString(event))
    #                         # print(eventValueToString(event))
    #                         if event.value == 0:
    #                             xbmc.release_button()
    #                         elif event.value == 1:
    #                             xbmc.send_button(map='KB', button='up')
    #
    #
    #
    #
    #             time.sleep(0.5)
    #
    #     except KeyboardInterrupt:
    #         pass
    #
    #     if xbmc is not None:
    #         xbmc.close()





