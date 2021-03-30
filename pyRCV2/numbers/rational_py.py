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

from fractions import Fraction
import math


class Rational(BasePyNum):
    """
	Wrapper for Python Fraction (rational arithmetic)
	"""

    __slots__ = []

    _py_class = Fraction  # For BasePyNum

    def pp(self, dp):
        """Overrides BasePyNum.pp"""
        # TODO: Work out if there is a better way of doing this
        return format(float(self.impl), '.{}f'.format(dp))

    def round(self, dps, mode):
        """Implements BaseNum.round"""
        factor = Fraction(10)**dps
        if mode == Rational.ROUND_DOWN:
            return Rational._from_impl(math.floor(self.impl * factor) / factor)
        elif mode == Rational.ROUND_HALF_UP:  # pragma: no cover
            raise NotImplementedError(
                'ROUND_HALF_UP is not implemented in Python Rational context')
        elif mode == Rational.ROUND_HALF_EVEN:
            return Rational._from_impl(round(self.impl * factor) / factor)
        elif mode == Rational.ROUND_UP:
            return Rational._from_impl(math.ceil(self.impl * factor) / factor)
        else:  # pragma: no cover
            raise ValueError('Invalid rounding mode')
