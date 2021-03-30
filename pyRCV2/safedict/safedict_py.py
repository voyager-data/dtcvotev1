#   pyRCV2: Preferential vote counting
#   Copyright © 2020  Lee Yingtong Li (RunasSudo)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.


class SafeDict:
    """Dictionary which can contain non-string keys in both Python and JS"""
    def __init__(self, params=None):
        if params:
            self.impl = {k: v for k, v in params}
        else:
            self.impl = {}

    def __getitem__(self, key):
        return self.impl[key]

    def __setitem__(self, key, value):
        self.impl[key] = value

    def __contains__(self, key):
        return key in self.impl

    def items(self):
        return self.impl.items()
