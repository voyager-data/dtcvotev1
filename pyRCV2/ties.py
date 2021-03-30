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
__pragma__('noskip')

from pyRCV2.random import SHARandom


class RequireInput(Exception):  # pragma: no cover
    # For JS only
    # Exceptions for control flow? In my code? It's more likely thank you think!
    def __init__(self, message):
        self.message = message


class TiesPrompt:
    """Prompt the user to break ties"""

    adverb = 'manually'

    def __init__(self):
        self.buffer = None

    def choose_lowest(self, l):
        if is_py:
            print('Multiple tied candidates:')
            for i, x in enumerate(l):
                print('{}. {}'.format(i + 1, x[0].name))

            while True:
                choice = input('Which candidate to select? ')
                try:
                    choice = int(choice)
                    if choice >= 1 and choice < len(l) + 1:
                        break
                except ValueError:
                    pass

            print()

            return l[choice - 1]
        else:  # pragma: no cover
            if self.buffer is not None:
                try:
                    choice = int(self.buffer)
                    if choice >= 1 and choice < len(l) + 1:
                        self.buffer = None
                        return l[choice - 1]
                except ValueError:
                    self.buffer = None
                    pass

            self.buffer = None

            # Require prompting
            message = 'Multiple tied candidates:\n'
            for i, x in enumerate(l):
                message += (i + 1) + '. ' + x[0].name + '\n'
            message += 'Which candidate to select?'

            raise RequireInput(message)

    def choose_highest(self, l):
        return self.choose_lowest(l)


class TiesBackwards:
    """
	Break ties based on the candidate who had the highest/lowest total at the end
	of the most recent stage where one candidate had a higher/lower total than
	all other tied candidates, if such a stage exists
	"""

    adverb = 'backwards'

    def __init__(self, counter):
        self.counter = counter

    def choose_lowest(self, l):
        for result in reversed(self.counter.step_results):
            __pragma__('opov')
            l2 = [(x, result.candidates[x[0]].votes) for x in l]
            l2.sort(key=lambda x: x[1])
            if l2[0][1] < l2[1][
                    1]:  # Did one candidate have fewer votes than the others?
                return l2[0][0]
            __pragma__('noopov')
        return None

    def choose_highest(self, l):
        for result in reversed(self.counter.step_results):
            __pragma__('opov')
            l2 = [(x, result.candidates[x[0]].votes) for x in l]
            l2.sort(key=lambda x: x[1], reverse=True)
            if l2[0][1] > l2[1][
                    1]:  # Did one candidate have more votes than the others?
                return l2[0][0]
            __pragma__('noopov')
        return None


class TiesForwards:
    """
	Break ties based on the candidate who had the highest/lowest total at the end
	of the earliest stage where one candidate had a higher/lower total than
	all other tied candidates, if such a stage exists
	"""

    adverb = 'forwards'

    def __init__(self, counter):
        self.counter = counter

    def choose_lowest(self, l):
        for result in self.counter.step_results:
            __pragma__('opov')
            l2 = [(x, result.candidates[x[0]].votes) for x in l]
            l2.sort(key=lambda x: x[1])
            if l2[0][1] < l2[1][
                    1]:  # Did one candidate have fewer votes than the others?
                return l2[0][0]
            __pragma__('noopov')
        return None

    def choose_highest(self, l):
        for result in self.counter.step_results:
            __pragma__('opov')
            l2 = [(x, result.candidates[x[0]].votes) for x in l]
            l2.sort(key=lambda x: x[1], reverse=True)
            if l2[0][1] > l2[1][
                    1]:  # Did one candidate have more votes than the others?
                return l2[0][0]
            __pragma__('noopov')
        return None


class TiesRandom:
    """Break ties randomly, using the SHARandom deterministic RNG"""

    adverb = 'randomly'

    def __init__(self, seed):
        self.random = SHARandom(seed)

    def choose_lowest(self, l):
        l.sort(key=lambda x: x[0].name)
        return l[self.random.next(len(l))]

    def choose_highest(self, l):
        l.sort(key=lambda x: x[0].name)
        return l[self.random.next(len(l))]
