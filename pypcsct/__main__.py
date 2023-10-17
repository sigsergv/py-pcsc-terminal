# Copyright 2023 Sergey Stolyarov <sergei@regolit.com>
#
# Distributed under New BSD License.
#
# https://opensource.org/license/bsd-3-clause/

import argparse
try:
    import gnureadline as readline
except ImportError:
    import readline
import os
import atexit
import re

from . import bertlv

from sys import exit
from smartcard.System import readers
from smartcard.CardRequest import CardRequest
from smartcard.CardConnection import CardConnection
from smartcard.util import toHexString, toBytes, PACK
from smartcard.Exceptions import CardConnectionException

def main():
    parser = argparse.ArgumentParser(
        prog='py-pcsc-terminal',
        description='CLI for PC/SC readers',
        epilog='')
    parser.add_argument('-l', '--list-readers', dest='list_readers', action='store_true', help='List available readers')
    parser.add_argument('-r', '--reader', dest='reader', metavar='READER', help='Reader to use: either index or full name, first reader is used by default.', default='0')

    args = parser.parse_args()

    init_readline()

    all_readers = readers()
    if args.list_readers:
        print('List of available readers:')
        for i,r in enumerate(all_readers):
            print(f'  {i}: {r}')
        return 0

    try:
        reader_idx = int(args.reader)
        if reader_idx < 0:
            reader_idx = None
    except ValueError:
        reader_idx = None

    reader = None
    if reader_idx is not None:
        try:
            reader = all_readers[reader_idx]
        except IndexError:
            pass

    for x in all_readers:
        if str(x) == args.reader:
            reader = x
            break

    if reader is None:
        print('Cannot find reader with this index or name.')
        return 1

    cardrequest = CardRequest(timeout=None, readers=[reader])
    cardservice = cardrequest.waitforcard()
    cardservice.connection.connect()
    # start another thread that will monitor card removal

    print('Card connected, starting REPL shell.')
    print('Type "exit" or "quit" to exit program, or press Ctrl+D.')

    while True:
        try:
            cmd = input('APDU% ')
            # normalization
            # remove comments starting with '#'
            cmd = re.sub('#.+', '', cmd)
            # remove leading and trailing spaces
            cmd = cmd.strip()
        except EOFError:
            break
        if cmd in ('exit', 'quit'):
            break
        if cmd == 'help':
            print_help()
            continue
        if cmd.startswith('bertlv-decode '):
            print_bertlv_data(toBytes(cmd[14:]))
            continue
        # ignored commands
        if cmd in ('',):
            continue
        try:
            apdu = toBytes(cmd)
            # output normalized query
            print('>', toHexString(apdu))
            response, sw1, sw2 = cardservice.connection.transmit(apdu)
            if len(response) == 0:
                print('< [empty response]', 'Status:', toHexString([sw1, sw2]))
            else:
                print('<', toHexString(response), 'Status:', toHexString([sw1, sw2]))
        except TypeError:
            print('>>> Invalid command')
        except CardConnectionException as e:
            print('<<< Reader communication error:', str(e))

    return 0


def init_readline():
    history_file = os.path.expanduser('~/.py-pcsc-terminal-history')
    def terminate():
        print('Exiting...')
        # filter out some history items
        #   starting with space
        for ind in range(readline.get_current_history_length(), 0, -1):
            item = readline.get_history_item(ind)
            if item is None:
                continue
            if item.startswith(' '):
                readline.remove_history_item(ind-1)

        readline.write_history_file(history_file)
    atexit.register(terminate)
    if os.path.exists(history_file):
        readline.read_history_file(history_file)
    readline.set_history_length(1000)
    readline.set_completer(completer)
    readline.set_completer_delims(' \t')
    readline.parse_and_bind('tab: complete')


def skip_command_from_history():
    readline.remove_history_item(readline.get_current_history_length()-1)


def print_bertlv_data(b):
    def print_tlv(tlv, depth):
        prefix = '  ' * depth
        print(prefix, end='')
        print(f'0x{tlv.tag:X}', end='')
        if tlv.encoding == bertlv.Tlv.PRIMITIVE:
            print(': (RAW) ' + toHexString(tlv.value))
        else:
            print('')
            for x in tlv.value:
                print_tlv(x, depth + 1)

    try:
        tlv_objects = bertlv.parse_bytes(b)
        for tlv in tlv_objects:
            print_tlv(tlv, 0)
    except TypeError as e:
        print('>>> Invalid input data')


def print_help():
    print('Additional commands:')
    print('  bertlv-decode BYTES')


ALL_COMMANDS = ('bertlv-decode',)

def completer(text, state):
    candidates = []
    for x in ALL_COMMANDS:
        if x.startswith(text):
            candidates.append(x)
    if state > len(candidates) - 1:
        return None
    return candidates[state]


if __name__ == '__main__':
    response = main()
    exit(response)
