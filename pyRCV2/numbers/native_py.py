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

from pyRCV2.numbers.base import BasePyNum, compatible_types

import math


class Native(BasePyNum):
    """
	Wrapper for Python float (naive floating-point arithmetic)
	"""

    __slots__ = []

    _py_class = float  # For BasePyNum

    def round(self, dps, mode):
        """Implements BaseNum.round"""
        factor = 10**dps
        if mode == Native.ROUND_DOWN:
            return Native._from_impl(math.floor(self.impl * factor) / factor)
        elif mode == Native.ROUND_HALF_UP:  # pragma: no cover
            raise NotImplementedError(
                'ROUND_HALF_UP is not implemented in Python Native context')
        elif mode == Native.ROUND_HALF_EVEN:
            return Native._from_impl(round(self.impl * factor) / factor)
        elif mode == Native.ROUND_UP:
            return Native._from_impl(math.ceil(self.impl * factor) / factor)
        else:  # pragma: no cover
            raise ValueError('Invalid rounding mode')
