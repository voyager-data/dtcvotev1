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

import decimal

_quantize_exp = decimal.Decimal('10')**-6


def _fixed_set_dps(dps):
    global _quantize_exp
    _quantize_exp = decimal.Decimal('10')**-dps


class Fixed(BasePyNum):
    """
	Wrapper for Python Decimal (for fixed-point arithmetic)
	"""

    __slots__ = []

    _py_class = decimal.Decimal  # For BasePyNum

    ROUND_DOWN = decimal.ROUND_DOWN
    ROUND_HALF_UP = decimal.ROUND_HALF_UP
    ROUND_HALF_EVEN = decimal.ROUND_HALF_EVEN
    ROUND_UP = decimal.ROUND_UP

    @classmethod
    def _to_impl(cls, value):
        """Overrides BasePyNum._to_impl"""
        return decimal.Decimal(value).quantize(_quantize_exp)

    @classmethod
    def _truediv_impl(cls, i1, i2):
        """Implements BaseNum._truediv_impl"""
        return (i1 / i2).quantize(_quantize_exp)

    @compatible_types
    def __itruediv__(self, other):
        """Overrides BaseNum.__itruediv__"""
        self.impl = (self.impl / other.impl).quantize(_quantize_exp)
        return self

    def round(self, dps, mode):
        """Implements BaseNum.round"""
        return Fixed._from_impl(
            self.impl.quantize(decimal.Decimal('10')**-dps, mode))
