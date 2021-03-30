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

import pyRCV2.blt
import pyRCV2.model
import pyRCV2.numbers

from pyRCV2.method.gregory import UIGSTVCounter, WIGSTVCounter, EGSTVCounter
from pyRCV2.method.meek import MeekSTVCounter
from pyRCV2.model import CandidateState
from pyRCV2.ties import TiesBackwards, TiesForwards, TiesPrompt, TiesRandom

import sys


def add_parser(subparsers):
    parser = subparsers.add_parser('stv', help='single transferable vote')
    parser.add_argument('file', help='path to BLT file')

    parser.add_argument('--quota',
                        '-q',
                        choices=['droop', 'droop_exact', 'hare', 'hare_exact'],
                        default='droop',
                        help='quota calculation (default: droop)')
    parser.add_argument('--quota-criterion',
                        '-c',
                        choices=['geq', 'gt'],
                        default='geq',
                        help='quota criterion (default: geq)')
    parser.add_argument(
        '--quota-mode',
        choices=['static', 'progressive', 'ers97'],
        default='static',
        help='whether to apply a form of progressive quota (default: static)')
    parser.add_argument(
        '--no-bulk-elect',
        action='store_true',
        help='disable bulk election unless absolutely required')
    parser.add_argument('--bulk-exclude',
                        action='store_true',
                        help='use bulk exclusion')
    parser.add_argument('--defer-surpluses',
                        action='store_true',
                        help='defer surplus transfers if possible')
    parser.add_argument('--numbers',
                        '-n',
                        choices=['fixed', 'gfixed', 'rational', 'native'],
                        default='fixed',
                        help='numbers mode (default: fixed)')
    parser.add_argument('--decimals',
                        type=int,
                        default=5,
                        help='decimal places if --numbers fixed (default: 5)')
    #parser.add_argument('--no-round-quota', action='store_true', help='do not round the quota')
    parser.add_argument('--round-quota',
                        type=int,
                        help='round quota to specified decimal places')
    parser.add_argument('--round-votes',
                        type=int,
                        help='round votes to specified decimal places')
    parser.add_argument(
        '--round-tvs',
        type=int,
        help='round transfer values to specified decimal places')
    parser.add_argument(
        '--round-weights',
        type=int,
        help='round ballot weights to specified decimal places')
    parser.add_argument(
        '--surplus-order',
        '-s',
        choices=['size', 'order'],
        default='size',
        help=
        'whether to distribute surpluses by size or by order of election (default: size)'
    )
    parser.add_argument(
        '--method',
        '-m',
        choices=['wig', 'uig', 'eg', 'meek'],
        default='wig',
        help=
        'method of transferring surpluses (default: wig - weighted inclusive Gregory)'
    )
    parser.add_argument(
        '--transferable-only',
        action='store_true',
        help='examine only transferable papers during surplus distributions')
    parser.add_argument(
        '--exclusion',
        choices=['one_round', 'parcels_by_order', 'by_value', 'wright'],
        default='one_round',
        help='how to perform exclusions (default: one_round)')
    parser.add_argument('--ties',
                        '-t',
                        action='append',
                        choices=['backwards', 'forwards', 'prompt', 'random'],
                        default=None,
                        help='how to resolve ties (default: prompt)')
    parser.add_argument(
        '--random-seed',
        default=None,
        help='arbitrary string used to seed the RNG for random tie breaking')
    parser.add_argument('--hide-excluded',
                        action='store_true',
                        help='hide excluded candidates from results report')
    parser.add_argument('--sort-votes',
                        action='store_true',
                        help='sort candidates by votes in results report')
    parser.add_argument(
        '--pp-decimals',
        type=int,
        default=2,
        help=
        'print votes to specified decimal places in results report (default: 2)'
    )


def print_step(args, stage, result):
    print('{}. {}'.format(stage, result.comment))

    if result.logs:
        print(' '.join(result.logs))

    results = list(result.candidates.items())
    if args.sort_votes:
        results.sort(key=lambda x: x[1].votes, reverse=True)

    for candidate, count_card in results:
        state = None
        if count_card.state == pyRCV2.model.CandidateState.ELECTED or count_card.state == pyRCV2.model.CandidateState.PROVISIONALLY_ELECTED or count_card.state == pyRCV2.model.CandidateState.DISTRIBUTING_SURPLUS:
            if args.method == 'meek':
                state = 'ELECTED {} (kv = {})'.format(
                    count_card.order_elected,
                    count_card.keep_value.pp(args.pp_decimals))
            else:
                state = 'ELECTED {}'.format(count_card.order_elected)
        elif count_card.state == pyRCV2.model.CandidateState.EXCLUDED or count_card.state == pyRCV2.model.CandidateState.EXCLUDING:
            state = 'Excluded {}'.format(-count_card.order_elected)
        elif count_card.state == pyRCV2.model.CandidateState.WITHDRAWN:
            state = 'Withdrawn'

        ppVotes = count_card.votes.pp(args.pp_decimals)
        ppTransfers = count_card.transfers.pp(args.pp_decimals)

        if state is None:
            print('- {}: {} ({})'.format(candidate.name, ppVotes, ppTransfers))
        else:
            if not (
                    args.hide_excluded and
                (count_card.state == pyRCV2.model.CandidateState.EXCLUDED
                 or count_card.state == pyRCV2.model.CandidateState.EXCLUDING)
                    and float(ppVotes) == 0 and float(ppTransfers) == 0):
                print('- {}: {} ({}) - {}'.format(candidate.name, ppVotes,
                                                  ppTransfers, state))

    print('Exhausted: {} ({})'.format(
        result.exhausted.votes.pp(args.pp_decimals),
        result.exhausted.transfers.pp(args.pp_decimals)))
    print('Loss to fraction: {} ({})'.format(
        result.loss_fraction.votes.pp(args.pp_decimals),
        result.loss_fraction.transfers.pp(args.pp_decimals)))
    print('Total votes: {}'.format(result.total.pp(args.pp_decimals)))

    if args.quota_mode == 'ers97' and result.vote_required_election < result.quota:
        print('Vote required for election: {}'.format(
            result.vote_required_election.pp(args.pp_decimals)))
    else:
        print('Quota: {}'.format(result.quota.pp(args.pp_decimals)))

    print()


def main(args):
    # Set settings
    if args.numbers == 'native':
        pyRCV2.numbers.set_numclass(pyRCV2.numbers.Native)
    elif args.numbers == 'rational':
        pyRCV2.numbers.set_numclass(pyRCV2.numbers.Rational)
    elif args.numbers == 'fixed':
        pyRCV2.numbers.set_numclass(pyRCV2.numbers.Fixed)
        pyRCV2.numbers.set_dps(args.decimals)
    elif args.numbers == 'gfixed':
        pyRCV2.numbers.set_numclass(pyRCV2.numbers.FixedGuarded)
        pyRCV2.numbers.set_dps(args.decimals)

    with open(args.file, 'r') as f:
        election = pyRCV2.blt.readBLT(f.read())

    # Create counter
    if args.method == 'uig':
        counter = UIGSTVCounter(election, vars(args))
    elif args.method == 'eg':
        counter = EGSTVCounter(election, vars(args))
    elif args.method == 'meek':
        counter = MeekSTVCounter(election, vars(args))
    else:
        counter = WIGSTVCounter(election, vars(args))

    #if args.no_round_quota:
    #	counter.options['round_quota'] = None

    if args.ties is None:
        args.ties = ['prompt']

    counter.options['ties'] = []
    for t in args.ties:
        if t == 'backwards':
            counter.options['ties'].append(TiesBackwards(counter))
        elif t == 'forwards':
            counter.options['ties'].append(TiesForwards(counter))
        elif t == 'prompt':
            counter.options['ties'].append(TiesPrompt())
        elif t == 'random':
            if args.random_seed is None:
                print(
                    'A --random-seed is required to use random tie breaking.')
                sys.exit(1)
            counter.options['ties'].append(TiesRandom(args.random_seed))

    counter.options['bulk_elect'] = not args.no_bulk_elect
    counter.options[
        'papers'] = 'transferable' if args.transferable_only else 'both'

    # Print report
    print(
        'Count computed by pyRCV2 (development version). Read {} ballots from "{}" for election "{}". There are {} candidates for {} vacancies. Counting using options "{}".'
        .format(
            sum((b.value for b in election.ballots),
                pyRCV2.numbers.Num(0)).pp(0), args.file, election.name,
            len(election.candidates), election.seats,
            counter.describe_options()))
    print()

    # Reset
    stage = 1
    result = counter.reset()

    print_step(args, stage, result)

    # Step election
    while True:
        stage += 1
        result = counter.step()

        if isinstance(result, pyRCV2.model.CountCompleted):
            break

        print_step(args, stage, result)

    print('Count complete. The winning candidates are, in order of election:')
    for x in sorted(((c, cc) for c, cc in result.candidates.items()
                     if cc.state == CandidateState.ELECTED),
                    key=lambda x: x[1].order_elected):
        print('{}. {}'.format(x[1].order_elected, x[0].name))
