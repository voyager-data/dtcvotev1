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

__pragma__ = lambda x: None
is_py = False
__pragma__('skip')
is_py = True
__pragma__('noskip')

# CLASS DEFINITIONS

if is_py:
    __pragma__('skip')
    from pyRCV2.numbers.fixed_py import Fixed, _fixed_set_dps
    from pyRCV2.numbers.gfixed_py import FixedGuarded, _gfixed_set_dps
    from pyRCV2.numbers.native_py import Native
    from pyRCV2.numbers.rational_py import Rational
    __pragma__('noskip')
else:  # pragma: no cover
    from pyRCV2.numbers.fixed_js import Fixed, _fixed_set_dps
    from pyRCV2.numbers.gfixed_js import FixedGuarded, _gfixed_set_dps
    from pyRCV2.numbers.native_js import Native
    from pyRCV2.numbers.rational_js import Rational
    from pyRCV2.numbers.string_js import StringNum

# GLOBALS

_numclass = Native


def set_numclass(cls):
    global _numclass
    _numclass = cls


def Num(val):
    return _numclass(val)


_dps = 6


def set_dps(dps):
    global _dps
    _dps = dps

    if _numclass is Fixed:
        _fixed_set_dps(dps)
    elif _numclass is FixedGuarded:
        _gfixed_set_dps(dps)


def get_dps():
    return _dps
