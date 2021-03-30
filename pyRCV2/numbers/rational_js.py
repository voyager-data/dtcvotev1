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


class Rational(BaseNum):
    """
	Wrapper for BigRational.js (rational arithmetic)
	"""
    @classmethod
    def _to_impl(cls, value):
        """Implements BaseNum._to_impl"""
        return bigRat(value)

    def pp(self, dp):
        """Implements BaseNum.pp"""
        # FIXME: This will fail for numbers which cannot be represented as a JavaScript number
        return self.impl.valueOf().toFixed(dp)

    @classmethod
    def _add_impl(cls, i1, i2):
        """Implements BaseNum._add_impl"""
        return i1.add(i2)

    @classmethod
    def _sub_impl(cls, i1, i2):
        """Implements BaseNum._sub_impl"""
        return i1.subtract(i2)

    @classmethod
    def _mul_impl(cls, i1, i2):
        """Implements BaseNum._mul_impl"""
        return i1.multiply(i2)

    @classmethod
    def _truediv_impl(cls, i1, i2):
        """Implements BaseNum._truediv_impl"""
        return i1.divide(i2)

    @compatible_types
    def __eq__(self, other):
        """Implements BaseNum.__eq__"""
        return self.impl.equals(other.impl)

    @compatible_types
    def __gt__(self, other):
        """Implements BaseNum.__gt__"""
        return self.impl.greater(other.impl)

    @compatible_types
    def __ge__(self, other):
        """Implements BaseNum.__ge__"""
        return self.impl.greaterOrEquals(other.impl)

    @compatible_types
    def __lt__(self, other):
        """Implements BaseNum.__lt__"""
        return self.impl.lesser(other.impl)

    @compatible_types
    def __le__(self, other):
        """Implements BaseNum.__le__"""
        return self.impl.lesserOrEquals(other.impl)

    def __floor__(self):
        """Overrides BaseNum.__floor__"""
        return Rational._from_impl(self.impl.floor())

    def __pow__(self, power):
        """Implements BaseNum.__pow__"""
        return Rational._from_impl(self.impl.pow(power))

    def round(self, dps, mode):
        """Implements BaseNum.round"""
        factor = bigRat(10).pow(dps)
        if mode == Rational.ROUND_DOWN:
            return Rational._from_impl(
                self.impl.multiply(factor).floor().divide(factor))
        elif mode == Rational.ROUND_HALF_UP:
            return Rational._from_impl(
                self.impl.multiply(factor).round().divide(factor))
        elif mode == Rational.ROUND_HALF_EVEN:
            raise NotImplementedError(
                'ROUND_HALF_EVEN is not implemented in JS Native context')
        elif mode == Rational.ROUND_UP:
            return Rational._from_impl(
                self.impl.multiply(factor).ceil().divide(factor))
        else:
            raise ValueError('Invalid rounding mode')
