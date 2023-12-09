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

import sys
import os
import json
import argparse

from libs.kodibtforwarder import KodiBTForwarder


def getDefaultConfigFile():
    if sys.platform == "linux" or sys.platform == "linux2":
        return '/etc/kodibluetoothforwarder.config'

    elif sys.platform == "darwin":
        # MAC OS X
        return None

    elif sys.platform == "win32":
        return 'C:\\python\\etc\\kodibluetoothforwarder.config'

    return None


def getDefaultLogFile():
    if sys.platform == "linux" or sys.platform == "linux2":
        return '/var/log/kodibluetoothforwarder.log'

    elif sys.platform == "darwin":
        # MAC OS X
        return None

    elif sys.platform == "win32":
        return 'C:\\python\\log\\kodibluetoothforwarder.log'

    return None


def getConfig(args):
    _config = {}
    config_file = args.config
    if os.path.isfile(config_file):
        with open(config_file) as json_data_file:
            _config = json.load(json_data_file)

    if 'controller' not in _config:
        _config['controller'] = {}

    if 'xbmc' not in _config:
        _config['xbmc'] = {}

    if 'log' not in _config:
        _config['log'] = {}

    if args.controller:
        _config['controller']['mac'] = args.controller

    if args.mapping:
        _config['controller']['mapping'] = args.mapping

    if args.xbmchost:
        _config['xbmc']['host'] = args.xbmchost

    if args.xbmcwebport:
        _config['xbmc']['webport'] = args.xbmcwebport

    if args.xbmceventserverport:
        _config['xbmc']['eventserverport'] = args.xbmceventserverport

    if args.xbmcuser:
        _config['xbmc']['user'] = args.xbmcuser

    if args.xbmcpass:
        _config['xbmc']['password'] = args.xbmcpass

    if args.log_file:
        _config['log']['filename'] = args.log_file

    if args.log_level:
        _config['log']['level'] = args.log_level

    if not _config['log'].get('filename'):
        _config['log']['filename'] = getDefaultLogFile()

    if not _config['log'].get('level'):
        _config['log']['level'] = 'INFO'

    return _config


def validateConfig(_config):
    if _config is None:
        print("broken config")
        return False

    if _config.get('controller') is None:
        print("broken config (controller)")
        return False

    if _config.get('xbmc') is None:
        print("broken config (xbmc)")
        return False

    if _config.get('log') is None:
        print("broken config (log)")
        return False

    if config['controller'].get('mac') is None:
        print("broken config (controller.mac)")
        return False

    if config['controller'].get('mapping') is None:
        print("broken config (controller.mapping)")
        return False

    if config['xbmc'].get('host') is None:
        print("broken config (xbmc.host)")
        return False

    if config['xbmc'].get('webport') is None:
        print("broken config (xbmc.webport)")
        return False

    if config['xbmc'].get('eventserverport') is None:
        print("broken config (xbmc.eventserverport)")
        return False

    if config['log'].get('filename') is None:
        print("broken config (log.filename)")
        return False

    if config['log'].get('level') is None:
        print("broken config (log.level)")
        return False

    return True


def setCurrentDirectory():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(scriptdir)


if __name__ == '__main__':
    setCurrentDirectory()
    parser = argparse.ArgumentParser(
        description='runner',
        epilog="That's all folks"
    )

    parser.add_argument('--config',
                        help='manual config file',
                        default=getDefaultConfigFile(),
                        type=str)

    parser.add_argument( '--controller',
                        help='controller mac',
                        type=str)

    parser.add_argument('--xbmchost',
                        help='xbmc host (default=127.0.0.1)',
                        default='127.0.0.1',
                        type=str)

    parser.add_argument('--xbmcwebport',
                        help='xbmc web port (default=8080)',
                        default=8080,
                        type=int)

    parser.add_argument('--xbmceventserverport',
                        help='xbmc event server port (default=9777)',
                        default=9777,
                        type=int)

    parser.add_argument('--xbmcuser',
                        help='xbmc user',
                        type=str)

    parser.add_argument('--xbmcpass',
                        help='xbmc password',
                        type=str)

    parser.add_argument('--mapping',
                        help='mapping',
                        type=str)

    parser.add_argument('--log-file',
                        dest='log_file',
                        help='manual log file',
                        default=getDefaultLogFile(),
                        type=str)

    parser.add_argument('-ll', '--log-level',
                        dest='log_level',
                        metavar='log level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        type=str)

    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit()

    config = getConfig(args)
    if not validateConfig(config):
        sys.exit()

    app = KodiBTForwarder(config)
    app.run()

