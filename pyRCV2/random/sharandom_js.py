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

if __pragma__('js', '{}', 'typeof(bigInt)') != 'undefined':
    _MAX_VAL = bigInt(2).pow(256).subtract(1)
else:
    # Fail gracefully if dependencies not present
    _MAX_VAL = None


class SHARandom:
    MAX_VAL = _MAX_VAL

    def __init__(self, seed):
        self.seed = seed
        self.ctr = 0

    def next(self, modulus):
        val = bigInt(
            sjcl.codec.hex.fromBits(
                sjcl.hash.sha256.hash(self.seed + ',' + str(self.ctr))), 16)
        self.ctr += 1

        if val.greaterOrEquals(
                SHARandom.MAX_VAL.divide(modulus).multiply(modulus)):
            # Discard this value to avoid bias
            return self.next(modulus)

        # Result is used to index arrays, etc. so result must be a JS number
        # TODO: Check for overflow
        return val.mod(modulus).toJSNumber()
