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
import os

import requests


class rpcclient:

    def __init__(self, host, port):
        self._api_url = "http://%s:%s/jsonrpc" % (host, port)

    def ping(self, _id=1):
        p = {"method": "JSONRPC.Ping", "id": _id, "jsonrpc": "2.0"}

        try:
            print("send ping")
            r = requests.post(self._api_url, json=p, timeout=3)
            if r.status_code == 200:
                return True
            elif r.status_code == 401:
                print("401")
                return False
            else:
                print("else")
                return False

        except os.error as e:
            pass

        print("end ping")
