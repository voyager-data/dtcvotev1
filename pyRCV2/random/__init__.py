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

__pragma__ = lambda x: None
is_py = False
__pragma__('skip')
is_py = True
__pragma__('noskip')

if is_py:
    __pragma__('skip')
    from pyRCV2.random.sharandom_py import SHARandom
    __pragma__('noskip')
else:  # pragma: no cover
    from pyRCV2.random.sharandom_js import SHARandom
