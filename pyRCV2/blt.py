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

from pyRCV2.model import Ballot, Candidate, Election
from pyRCV2.numbers import Num


class BLTException(Exception):
    pass


def readBLT(data):
    lines = data.split('\n')

    election = Election()

    # Read first line
    num_candidates = int(lines[0].strip().split(' ')[0])
    election.seats = int(lines[0].strip().split(' ')[1])

    # Read withdrawn candidates
    withdrawn = []
    i = 1
    if lines[i].strip().startswith('-'):
        withdrawn.extend([int(x[1:]) - 1 for x in lines[i].strip().split(' ')])
        i += 1

    # Read ballots
    ballot_data = []
    for j in range(i, len(lines)):
        if lines[j].strip() == '0':  # End of ballots
            break
        bits = lines[j].strip().split(' ')
        preferences = [int(x) - 1 for x in bits[1:] if x != '0']
        ballot_data.append((bits[0], preferences))

    # Read candidates
    for k in range(j + 1, j + 1 + num_candidates):
        election.candidates.append(Candidate(lines[k].strip()[1:-1]))

    # Read name
    if j + 1 + num_candidates < len(lines):
        election.name = lines[j + 1 + num_candidates].strip()[1:-1]

    # Any additional data?
    if len(lines) > j + 2 + num_candidates and len(
            lines[j + 2 + num_candidates].strip()) > 0:
        raise BLTException('Unexpected data at end of BLT file')
    if len(lines) > j + 3 + num_candidates:
        raise BLTException('Unexpected data at end of BLT file')

    # Process ballots
    for ballot in ballot_data:
        preferences = [election.candidates[x] for x in ballot[1]]
        election.ballots.append(Ballot(Num(ballot[0]), preferences))

    # Process withdrawn candidates
    election.withdrawn = [election.candidates[x] for x in withdrawn]

    return election


def writeBLT(election, stringify=str):
    lines = []

    lines.append('{} {}'.format(len(election.candidates), election.seats))

    if len(election.withdrawn) > 0:
        lines.append(' '.join([
            '-{}'.format(election.candidates.index(candidate) + 1)
            for candidate in election.withdrawn
        ]))

    for ballot in election.ballots:
        if ballot.preferences:
            lines.append('{} {} 0'.format(
                stringify(ballot.value), ' '.join(
                    str(election.candidates.index(x) + 1)
                    for x in ballot.preferences)))
        else:
            lines.append('{} 0'.format(stringify(ballot.value)))

    lines.append('0')

    for candidate in election.candidates:
        lines.append('"{}"'.format(candidate.name))

    lines.append('"{}"'.format(election.name))

    return '\n'.join(lines)
