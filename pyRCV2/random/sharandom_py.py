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

import hashlib


class SHARandom:
    MAX_VAL = 2**256 - 1

    def __init__(self, seed):
        self.seed = seed
        self.ctr = 0

    def next(self, modulus):
        c = hashlib.sha256()
        c.update((self.seed + ',' + str(self.ctr)).encode('utf-8'))
        self.ctr += 1
        val = int.from_bytes(c.digest(), byteorder='big', signed=False)

        if val >= (SHARandom.MAX_VAL // modulus) * modulus:
            # Discard this value to avoid bias
            return self.next(modulus)

        return val % modulus
