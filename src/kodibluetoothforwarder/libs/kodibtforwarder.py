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

###
### flags
### --------------------------------------
### KEY_LEFTCTRL    --> 0b00000001   (1)
### KEY_LEFTSHIFT   --> 0b00000010   (2)
### KEY_RIGHTSHIFT  --> 0b00000100   (4)
### KEY_LEFTALT     --> 0b00001000   (8)
### KEY_RIGHTALT    --> 0b00010000  (16)
### KEY_RIGHTCTRL   --> 0b00100000  (32)
### KEY_LEFTMETA    --> 0b01000000  (64)
### KEY_RIGHTMETA   --> 0b10000000 (128)

import json

import evdev
import asyncio
from socket import *
from os.path import isfile

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
        self._mapping = None

    async def ping_eventserver(self):
        while True:
            if self._xbmc_connected:
                self._xbmc.ping()

            await asyncio.sleep(50)

    def getMappingEntry(self, key, flags=0):
        if key in self._mapping:
            for e in self._mapping[key]:
                if e['flags'] == flags:
                    return e

        return None

    async def monitorController(self):
        while True:
            if self._controller is None:
                self._controller = getBluetoothController(self._config['controller']['mac'])

            if self._controller is not None:
                flags = 0
                try:
                    async for event in self._controller.async_read_loop():
                        if event.type == evdev.ecodes.EV_KEY:
                            if self._xbmc_connected:
                                if event.value != 2:
                                    key = eventCodeToString(event)
                                    key_flag = getKeyFlag(key)
                                    flags = flags | key_flag
                                    if key_flag == 0:
                                        print(flags)
                                        entry = self.getMappingEntry(eventCodeToString(event), flags)
                                        if entry is not None:
                                            if 'key' in entry and entry['key']:
                                                if event.value == 0:
                                                    flags = 0
                                                    self._xbmc.release_button()
                                                elif event.value == 1:
                                                    print(key)
                                                    self._xbmc.send_button(map='KB', button=entry['key'])

                except error as e:
                    self._controller = None

            await asyncio.sleep(0.5)

    async def checkXBMC(self):
        host = self._config['xbmc']['host']
        port = self._config['xbmc']['eventserverport']
        rclient = rpcclient(host, self._config['xbmc']['webport'])
        while True:
            if self._controller is not None:
                if not self._xbmc_connected:
                    if rclient.ping():
                        self._xbmc = XBMCClient(host=host, port=port)
                        self._xbmc.connect()
                        self._xbmc_connected = True

                else:
                    if not rclient.ping():
                        self._xbmc_connected = False

                if not self._xbmc_connected:
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(120)

            else:
                await asyncio.sleep(0.5)

    def getMapping(self):
        m = {}
        cwd = os.path.join(os.getcwd(), 'mappings')
        for f in os.listdir(cwd):
            mapping = os.path.join(cwd, f)
            if isfile(mapping):
                try:
                    with open(mapping) as json_data_file:
                        m = json.load(json_data_file)

                    if 'name' in m:
                        if m['name'] == self._config['controller']['mapping'] and 'mapping' in m:
                            self._mapping = m['mapping']
                            for key in self._mapping:
                                for e in self._mapping[key]:
                                    if 'flags' not in e:
                                        e['flags'] = 0
                                        # self._mapping[key]['flags'] = 0
                            return True

                except json.decoder.JSONDecodeError as e:
                    pass

        return False

    def run(self):
        if not self.getMapping():
            sys.exit()

        eventloop = asyncio.get_event_loop()
        eventloop.create_task(wakeup_loop())
        eventloop.create_task(self.monitorController())
        eventloop.create_task(self.checkXBMC())
        eventloop.create_task(self.ping_eventserver())

        try:
            eventloop.run_forever()
        except KeyboardInterrupt:
            pass

