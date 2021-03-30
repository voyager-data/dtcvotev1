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


class Native(BaseNum):
    """
	Wrapper for JS numbers (naive floating-point arithmetic)
	"""
    @classmethod
    def _to_impl(cls, value):
        """Implements BaseNum._to_impl"""
        return parseFloat(value)

    def pp(self, dp):
        """Implements BaseNum.pp"""
        return self.impl.toFixed(dp)

    @classmethod
    def _add_impl(cls, i1, i2):
        """Implements BaseNum._add_impl"""
        return i1 + i2

    @classmethod
    def _sub_impl(cls, i1, i2):
        """Implements BaseNum._sub_impl"""
        return i1 - i2

    @classmethod
    def _mul_impl(cls, i1, i2):
        """Implements BaseNum._mul_impl"""
        return i1 * i2

    @classmethod
    def _truediv_impl(cls, i1, i2):
        """Implements BaseNum._truediv_impl"""
        return i1 / i2

    @compatible_types
    def __eq__(self, other):
        """Implements BaseNum.__eq__"""
        return self.impl == other.impl

    @compatible_types
    def __ne__(self, other):
        """Overrides BaseNum.__ne__"""
        return self.impl != other.impl

    @compatible_types
    def __gt__(self, other):
        """Implements BaseNum.__gt__"""
        return self.impl > other.impl

    @compatible_types
    def __ge__(self, other):
        """Implements BaseNum.__ge__"""
        return self.impl >= other.impl

    @compatible_types
    def __lt__(self, other):
        """Implements BaseNum.__lt__"""
        return self.impl < other.impl

    @compatible_types
    def __le__(self, other):
        """Implements BaseNum.__le__"""
        return self.impl <= other.impl

    def __floor__(self):
        """Overrides BaseNum.__floor__"""
        return Native._from_impl(Math.floor(self.impl))

    def __pow__(self, power):
        """Implements BaseNum.__pow__"""
        return Native._from_impl(Math.pow(self.impl, power))

    def round(self, dps, mode):
        """Implements BaseNum.round"""
        if mode == Native.ROUND_DOWN:
            return Native._from_impl(
                Math.floor(self.impl * Math.pow(10, dps)) / Math.pow(10, dps))
        elif mode == Native.ROUND_HALF_UP:
            return Native._from_impl(
                Math.round(self.impl * Math.pow(10, dps)) / Math.pow(10, dps))
        elif mode == Native.ROUND_HALF_EVEN:
            raise NotImplementedError(
                'ROUND_HALF_EVEN is not implemented in JS Native context')
        elif mode == Native.ROUND_UP:
            return Native._from_impl(
                Math.ceil(self.impl * Math.pow(10, dps)) / Math.pow(10, dps))
        else:
            raise ValueError('Invalid rounding mode')
