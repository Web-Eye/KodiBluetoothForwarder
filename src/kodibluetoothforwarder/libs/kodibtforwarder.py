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
import signal

from socket import *
from os.path import isfile

from .common.tools import *
from .core.xbmcclient import *
from .core.rpcclient import *


# async def wakeup_loop():
#     while True:
#         await asyncio.sleep(1)


class KodiBTForwarder:

    def __init__(self, config, logger):
        self._config = config
        self._logger = logger
        self._xbmc = None
        self._xbmc_connected = False
        self._controller = None
        self._mapping = None

        host = self._config['xbmc']['host']
        port = self._config['xbmc']['webport']
        self._rclient = rpcclient(host, port, self._logger)

    async def ping_eventserver(self):
        self._logger.debug('starting ping_eventserver task')
        while True:
            if self._xbmc_connected:
                self._logger.debug('ping_eventserver: ping')
                self._xbmc.ping()

            await asyncio.sleep(50)

    def getMappingEntry(self, key, flags=0):
        if key in self._mapping:
            for e in self._mapping[key]:
                if e['flags'] == flags:
                    return e

        return None

    async def monitorController(self):
        self._logger.debug('starting monitorController task')
        while True:
            if self._controller is None:
                self._controller = getBluetoothController(self._config['controller']['mac'])

            if self._controller is not None:
                flags = 0
                try:
                    async for event in self._controller.async_read_loop():
                        if event.type == evdev.ecodes.EV_KEY:
                            if event.value != 2:
                                key = eventCodeToString(event)
                                if event.value == 0:
                                    self._logger.debug(f'Get Bluetooth event [release] key "{key}"')
                                elif event.value == 1:
                                    self._logger.debug(f'Get Bluetooth event [press] key "{key}"')
                                key_flag = getKeyFlag(key)
                                self._logger.debug(f'key_flag: {key_flag}; flags: {flags}; flags | key_flag: {flags | key_flag}')
                                flags = flags | key_flag

                                if key_flag == 0:
                                    entry = self.getMappingEntry(eventCodeToString(event), flags)
                                    if entry is not None:
                                        if 'key' in entry and entry['key']:
                                            if event.value == 0:
                                                flags = 0
                                                self.ConnectXBMC()
                                                if self._xbmc_connected:
                                                    self._logger.debug('Bluettoth send release all buttons')
                                                    self._xbmc.release_button()
                                            elif event.value == 1:
                                                self.ConnectXBMC()
                                                if self._xbmc_connected:
                                                    snd_key = entry['key']
                                                    self._logger.debug(f'Bluetooth send key "{snd_key}"')
                                                    self._xbmc.send_button(map='KB', button=snd_key)

                                        elif 'special' in entry and entry['special']:
                                            if event.value == 0:
                                                flags = 0
                                                self.handleSpecial(entry['special'])

                                        elif 'action' in entry and entry['action']:
                                            if event.value == 0:
                                                flags = 0
                                                self.handleAction(entry['action'])

                except error as e:
                    self._controller = None

            await asyncio.sleep(0.5)

    def ConnectXBMC(self):
        if not self._xbmc_connected:
            self._logger.debug('try to connect to xbmc')
            host = self._config['xbmc']['host']
            port = self._config['xbmc']['eventserverport']
            if self._rclient.ping():
                self._xbmc = XBMCClient(host=host, port=port, logger=self._logger)
                # self._xbmc.connect()
                self._xbmc_connected = True
                self._logger.info('XBMC is connected')

    def handleAction(self, msg):
        self.ConnectXBMC()
        if self._xbmc_connected:
            self._logger.debug(f'Send action "{msg}"')
            self._xbmc.send_action(msg)

    def handleSpecial(self, cmd):
        {
            'PowerOn': self.handlePowerOn,
            'PowerOff': self.handlePowerOff
        }[cmd]()

    def handlePowerOn(self):
        self._logger.debug(f'Handle special "PowerOn"')
        mac_address = self._config['xbmc']['mac']
        sendWOLPackage(mac_address)
        self._xbmc_connected = False

    def handlePowerOff(self):
        self._logger.debug(f'Handle special "PowerOff"')
        if not self._rclient.shutdown():
            pass
            # todo : do shutdown via ssh

        self._xbmc_connected = False
        self._logger.info('XBMC is disconnected')

    async def checkXBMC(self):
        self._logger.debug('starting checkXBMC task')
        while True:
            if self._controller is not None:
                if self._xbmc_connected:
                    if not self._rclient.ping():
                        self._xbmc_connected = False
                        self._logger.info('XBMC is disconnected')

            await asyncio.sleep(120)

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

                            return True

                except json.decoder.JSONDecodeError as e:
                    self._logger.error(f'getMapping (json.decoder.JSONDecodeError): {str(e)}')

        mp = self._config['controller']['mapping']
        self._logger.critical(f'getMapping "{mp}" was not found')
        return False

    async def shutdown(self, signal, loop):
        self._logger.info(f'Received exit signal {signal.name}...')
        self._logger.debug('shutting down tasks')
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()

    def run(self):
        if not self.getMapping():
            sys.exit()

        self._logger.info('starting [Kodi Bluetooth Forwarder] service.')

        eventloop = asyncio.get_event_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            eventloop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(s, eventloop)))
        queue = asyncio.Queue()

        try:
            # eventloop.create_task(wakeup_loop())
            eventloop.create_task(self.monitorController())
            eventloop.create_task(self.checkXBMC())
            eventloop.create_task(self.ping_eventserver())
            eventloop.run_forever()
        finally:
            eventloop.close()
            self._logger.info("Successfully shutdown [Kodi Bluetooth Forwarder] service.")


        