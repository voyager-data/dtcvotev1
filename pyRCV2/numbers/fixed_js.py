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

from pyRCV2.numbers.base import BaseNum, compatible_types

if __pragma__('js', '{}', 'typeof(bigInt)') != 'undefined':
    Big.DP = 6
else:
    # Fail gracefully if dependencies not present
    pass


def _fixed_set_dps(dps):
    Big.DP = dps


class Fixed(BaseNum):
    """
	Wrapper for big.js (fixed-point arithmetic)
	"""
    @classmethod
    def _to_impl(cls, value):
        """Implements BaseNum._to_impl"""
        return Big(value).round(Big.DP)

    def pp(self, dp):
        """Implements BaseNum.pp"""
        return self.impl.toFixed(dp)

    @classmethod
    def _add_impl(cls, i1, i2):
        """Implements BaseNum._add_impl"""
        return i1.plus(i2)

    @classmethod
    def _sub_impl(cls, i1, i2):
        """Implements BaseNum._sub_impl"""
        return i1.minus(i2)

    @classmethod
    def _mul_impl(cls, i1, i2):
        """Implements BaseNum._mul_impl"""
        return i1.times(i2)

    @classmethod
    def _truediv_impl(cls, i1, i2):
        """Implements BaseNum._truediv_impl"""
        return i1.div(i2)

    @compatible_types
    def __eq__(self, other):
        """Implements BaseNum.__eq__"""
        return self.impl.eq(other.impl)

    @compatible_types
    def __gt__(self, other):
        """Implements BaseNum.__gt__"""
        return self.impl.gt(other.impl)

    @compatible_types
    def __ge__(self, other):
        """Implements BaseNum.__ge__"""
        return self.impl.gte(other.impl)

    @compatible_types
    def __lt__(self, other):
        """Implements BaseNum.__lt__"""
        return self.impl.lt(other.impl)

    @compatible_types
    def __le__(self, other):
        """Implements BaseNum.__le__"""
        return self.impl.lte(other.impl)

    def __pow__(self, power):
        """Implements BaseNum.__pow__"""
        return Fixed._from_impl(self.impl.pow(power))

    def round(self, dps, mode):
        """Implements BaseNum.round"""
        return Fixed._from_impl(self.impl.round(dps, mode))
