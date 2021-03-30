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

from .cli import stv

import argparse

parser = argparse.ArgumentParser(
    prog='python -m pyRCV', description='pyRCV2: Preferential vote counting')
subparsers = parser.add_subparsers(title='method', dest='subcommand')

stv.add_parser(subparsers)

args = parser.parse_args()

if args.subcommand == 'stv':
    stv.main(args)
