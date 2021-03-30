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
import functools
import math

__pragma__('noskip')


def compatible_types(f):
    if is_py:
        __pragma__('skip')
        import os
        if 'PYTEST_CURRENT_TEST' in os.environ:

            @functools.wraps(f)
            def wrapper(self, other):
                if not isinstance(other, self.__class__):
                    raise ValueError(
                        'Attempt to operate on incompatible types')
                return f(self, other)

            return wrapper
        else:
            return f
        __pragma__('noskip')
    else:  # pragma: no cover
        # FIXME: Do we need to perform type checking in JS?
        return f


class BaseNum:
    __slots__ = [
        'impl'
    ]  # Optimisation to reduce overhead of initialising new object

    # These enum values may be overridden in subclasses depending on underlying library
    ROUND_DOWN = 0
    ROUND_HALF_UP = 1
    ROUND_HALF_EVEN = 2
    ROUND_UP = 3

    def __init__(self, value):
        if isinstance(value, self.__class__):
            self.impl = value.impl
        else:
            self.impl = self._to_impl(value)

    @classmethod
    def _to_impl(cls, value):
        """
		Internal use: Convert the given value to an impl
		Subclasses must override this method
		"""
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @classmethod
    def _from_impl(cls, impl):
        """Internal use: Return an instance directly from the given impl without performing checks"""
        if is_py:
            obj = cls.__new__(cls)
        else:
            # Transcrypt's __new__ (incorrectly) calls the constructor
            obj = __pragma__(
                'js', '{}',
                'Object.create (cls, {__class__: {value: cls, enumerable: true}})'
            )
        obj.impl = impl
        return obj

    def pp(self, dp):
        """
		Pretty print to specified number of decimal places
		Subclasses must override this method
		"""
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    # Implementation of arithmetic on impls
    # Subclasses must override these functions:

    @classmethod
    def _add_impl(cls, i1, i2):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @classmethod
    def _sub_impl(cls, i1, i2):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @classmethod
    def _mul_impl(cls, i1, i2):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @classmethod
    def _truediv_impl(cls, i1, i2):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @compatible_types
    def __eq__(self, other):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @compatible_types
    def __ne__(self, other):
        return not (self.__eq__(other))

    @compatible_types
    def __gt__(self, other):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @compatible_types
    def __ge__(self, other):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @compatible_types
    def __lt__(self, other):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    @compatible_types
    def __le__(self, other):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    def __pow__(self, power):
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    def round(self, dps, mode):
        """
		Round to the specified number of decimal places, using the ROUND_* mode specified
		Subclasses must override this method
		"""
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    # Implement various data model functions based on _*_impl

    @compatible_types
    def __add__(self, other):
        return self._from_impl(self._add_impl(self.impl, other.impl))

    @compatible_types
    def __sub__(self, other):
        return self._from_impl(self._sub_impl(self.impl, other.impl))

    @compatible_types
    def __mul__(self, other):
        return self._from_impl(self._mul_impl(self.impl, other.impl))

    @compatible_types
    def __truediv__(self, other):
        return self._from_impl(self._truediv_impl(self.impl, other.impl))

    @compatible_types
    def __iadd__(self, other):
        self.impl = self._add_impl(self.impl, other.impl)
        return self

    @compatible_types
    def __isub__(self, other):
        self.impl = self._sub_impl(self.impl, other.impl)
        return self

    @compatible_types
    def __imul__(self, other):
        self.impl = self._mul_impl(self.impl, other.impl)
        return self

    @compatible_types
    def __itruediv__(self, other):
        self.impl = self._truediv_impl(self.impl, other.impl)
        return self

    def __idiv__(self, other):
        # For Transcrypt
        return self.__itruediv__(other)

    def __floor__(self):
        return self.round(0, self.ROUND_DOWN)


class BasePyNum(BaseNum):
    """Helper class for Num wrappers of Python objects that already implement overloading"""

    __slots__ = []

    _py_class = None  # Subclasses must specify

    @classmethod
    def _to_impl(cls, value):
        """Implements BaseNum._to_impl"""
        return cls._py_class(value)

    def pp(self, dp):
        """Implements BaseNum.pp"""
        return format(self.impl, '.{}f'.format(dp))

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

    def __pow__(self, power):
        """Implements BaseNum.__pow__"""
        return self._from_impl(self.impl**power)

    @compatible_types
    def __iadd__(self, other):
        """Overrides BaseNum.__iadd__"""
        self.impl += other.impl
        return self

    @compatible_types
    def __isub__(self, other):
        """Overrides BaseNum.__isub__"""
        self.impl -= other.impl
        return self

    @compatible_types
    def __imul__(self, other):
        """Overrides BaseNum.__imul__"""
        self.impl *= other.impl
        return self

    @compatible_types
    def __itruediv__(self, other):
        """Overrides BaseNum.__itruediv__"""
        self.impl /= other.impl
        return self

    def __floor__(self):
        return self._from_impl(math.floor(self.impl))

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, str(self.impl))
