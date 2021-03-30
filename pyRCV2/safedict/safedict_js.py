#   pyRCV2: Preferential vote counting
#   Copyright © 2020–2021  Lee Yingtong Li (RunasSudo)
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
        self.impl = __new__(Map)

        if params:
            for k, v in params:
                self.impl.set(k, v)

    def __getitem__(self, key):
        return self.impl.js_get(key)

    def __setitem__(self, key, value):
        self.impl.set(key, value)

    def __contains__(self, key):
        return self.impl.has(key)

    def items(self):
        entries = self.impl.entries()  # Returns an Iterator
        return __pragma__('js', 'Array.from(entries)')
