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
import socket

import evdev
import asyncio
import signal
import paramiko
import subprocess

from socket import *
from os.path import isfile
from datetime import datetime, timedelta

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
        self._lstPowerOnTimestamp = None
        self._lstPowerOffTimestamp = None
        self._special_timeout = timedelta(seconds=30)
        self._lastKeyPress = None
        self._keyPressTimeOut = timedelta(milliseconds=40)

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

    def getMappingEntry(self, key, flags=0, eventType='RELEASE'):
        if key in self._mapping:
            for e in self._mapping[key]:
                if e['flags'] == flags and e['type'] == eventType:
                    return e

        return None

    async def monitorController(self, eventloop):
        self._logger.debug('starting monitorController task')
        while True:
            if self._controller is None:
                self._controller = getBluetoothController(self._config['controller']['mac'])

            if self._controller is not None:
                flags = 0
                last_event = 0
                try:
                    async for event in self._controller.async_read_loop():
                        if event.type == evdev.ecodes.EV_KEY:
                            key, key_flag, event_type = getEventData(event)
                            flags = flags | key_flag
                            if key_flag == 0:
                                self._logger.debug(f'Get Bluetooth event [{event_type}] key "{key}" ({flags})')

                                entry = self.getMappingEntry(key, flags, event_type)
                                if entry is not None:
                                    if 'key' in entry and entry['key']:
                                        if event_type == 'PRESS' or event_type == 'HOLD':
                                            self.ConnectXBMC()
                                            if self._xbmc_connected:
                                                last_event = 1
                                                snd_key = entry['key']
                                                self._logger.info(f'Bluetooth send key "{snd_key}"')
                                                self._xbmc.send_button(map='KB', button=snd_key)
                                                if event_type == 'PRESS':
                                                    self._lastKeyPress = datetime.now()

                                        elif event_type == 'RELEASE':
                                            flags = 0
                                            last_event = 0
                                            eventloop.create_task(self.releaseButtons(entry['key']))

                                    elif 'special' in entry and entry['special']:
                                        flags = 0
                                        last_event = 0
                                        self._lastKeyPress = None
                                        self.handleSpecial(entry['special'], eventloop)

                                    elif 'action' in entry and entry['action']:
                                        flags = 0
                                        last_event = 0
                                        self._lastKeyPress = None
                                        self.handleAction(entry['action'])

                                else:
                                    flags = 0
                                    if event_type == 'RELEASE' and last_event == 1:
                                        last_event = 0
                                        eventloop.create_task(self.releaseButtons())

                except error as e:
                    self._controller = None

            await asyncio.sleep(0.5)

    async def releaseButtons(self, snd_key=None):
        if self._lastKeyPress is not None:
            wait_time = (self._keyPressTimeOut - (datetime.now() - self._lastKeyPress)).total_seconds()
            if wait_time > 0:
                self._logger.debug(f'wait {int(wait_time * 1000)} ms before release Buttons')
                await asyncio.sleep(wait_time)
            self._lastKeyPress = None

        self.ConnectXBMC()
        if self._xbmc_connected:
            if snd_key is not None:
                self._logger.debug(f'Bluetooth send key "{snd_key}"')
                self._xbmc.send_button(map='KB', button=snd_key)

            self._logger.info('Bluetooth send "release all buttons"')
            self._xbmc.release_button()

    def ConnectXBMC(self):
        if not self._xbmc_connected:
            self._logger.debug('try to connect to xbmc')
            host = self._config['xbmc']['host']
            port = self._config['xbmc']['eventserverport']
            if self._rclient.ping():
                self._xbmc = XBMCClient(host=host, port=port, logger=self._logger)
                self._xbmc_connected = True
                self._logger.info('XBMC is connected')

    def handleAction(self, msg):
        self.ConnectXBMC()
        if self._xbmc_connected:
            self._logger.info(f'Send action "{msg}"')
            self._xbmc.send_action(msg)

    def handleSpecial(self, cmd, eventloop):
        # {
        #     'PowerOn': self.handlePowerOn,
        #     'PowerOff': eventloop.create_task(self.handlePowerOff)
        # }[cmd]()

        if cmd == "PowerOn":
            self.handlePowerOn()
        elif cmd == 'PowerOff':
            eventloop.create_task(self.handlePowerOff)

    def handlePowerOn(self):
        if self._lstPowerOnTimestamp is None or datetime.now() - self._lstPowerOnTimestamp > self._special_timeout:
            self._lstPowerOnTimestamp = datetime.now()
            self._logger.info(f'Handle special "PowerOn"')
            mac_address = self._config['xbmc']['mac']
            sendWOLPackage(mac_address)
            self._xbmc_connected = False

    async def handlePowerOff(self):
        if self._lstPowerOffTimestamp is None or datetime.now() - self._lstPowerOffTimestamp > self._special_timeout:
            self._lstPowerOffTimestamp = datetime.now()
            self._logger.info(f'Handle special "PowerOff"')
            if self._rclient.shutdown():
                await asyncio.sleep(5)

            if self._config['xbmc']['ssh'] is not None:
                hostname = self._config['xbmc']['host']
                port = self._config['xbmc']['ssh']['port']
                username = self._config['xbmc']['ssh']['username']
                password = self._config['xbmc']['ssh']['password']
                sudo_password = self._config['xbmc']['ssh']['sudo_password']
                self._logger.info('perform Shutdown via sshclient')

                self._logger.debug('setup sshclient')
                ssh_client = paramiko.SSHClient()
                self._logger.debug('add host key policy to sshclient')
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    self._logger.debug(f'sshclient.connect {hostname}:{port} via {username}:{password}')
                    ssh_client.connect(hostname=hostname, port=port, username=username, password=password)
                    self._logger.debug(f'sshclient.send "sudo shutdown now"')
                    stdin, stdout, stderr = ssh_client.exec_command("sudo  -S -p '' shutdown now")
                    self._logger.debug(f'sshclient.send "{sudo_password}"')
                    stdin.write(f'{sudo_password}\n')
                    stdin.flush()

                    if stdout is not None:
                        self._logger.debug(f'sshclient.receive (stdout): "{stdout.readlines()}"')
                    if stderr is not None:
                        self._logger.debug(f'sshclient.receive (stderr): "{stderr.readlines()}"')

                except paramiko.ssh_exception.BadHostKeyException as badhostEx:
                    self._logger.error(f'BadHostKeyException: {badhostEx}')

                except paramiko.ssh_exception.AuthenticationException as authEx:
                    self._logger.error(f'AuthenticationException: {authEx}')

                except paramiko.ssh_exception.UnableToAuthenticate as unableEx:
                    self._logger.error(f'UnableToAuthenticate: {unableEx}')

                except socket.error as socketEx:
                    self._logger.error(f'socket.error: {socketEx}')

                except paramiko.ssh_exception.NoValidConnectionsError as novalidConEx:
                    self._logger.error(f'NoValidConnectionsError: {novalidConEx}')

                except paramiko.ssh_exception.SSHException as sshEx:
                    self._logger.error(f'SSHException: {sshEx}')

            self._xbmc_connected = False
            self._logger.info('XBMC is disconnected')
            self.disconnectController()

    async def checkXBMC(self):
        self._logger.debug('starting checkXBMC task')
        while True:
            if self._controller is not None:
                if self._xbmc_connected:
                    if not self._rclient.ping():
                        self._xbmc_connected = False
                        self._logger.info('XBMC is disconnected')
                        self.disconnectController()

            await asyncio.sleep(120)

    def disconnectController(self):
        command = ['bluetoothctl', 'disconnect', self._config['controller']['mac']]
        self._logger.debug('run bluetoothctl to disconnect device')
        try:
            process = subprocess.run(command, capture_output=True, text=True)
            err = process.returncode
            if err != 0:
                self._logger.debug(f'stderr: {process.stderr}')
            else:
                self._logger.debug(f'stdout: {process.stdout}')

        except FileNotFoundError as ex:
            self._logger.debug('command not found')
            return False

    def getMapping(self):
        m = {}
        cwd = os.path.join(os.getcwd(), 'mappings')
        for f in os.listdir(cwd):
            mapping = os.path.join(cwd, f)
            if isfile(mapping) and mapping[-1] != '~':
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
                                    if 'type' not in e:
                                        e['type'] = 'PRESS'

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
            eventloop.create_task(self.monitorController(eventloop))
            eventloop.create_task(self.checkXBMC())
            eventloop.create_task(self.ping_eventserver())
            eventloop.run_forever()
        finally:
            eventloop.close()
            self._logger.info("Successfully shutdown [Kodi Bluetooth Forwarder] service.")


        