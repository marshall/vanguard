#!/usr/bin/env python
import argparse
import logging
import sys

import command
import config

def main():
    import log

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=None)
    parser.add_argument('-l', '--logfile', default=log.DEFAULT_FILENAME)
    parser.add_argument('command')

    args = parser.parse_args()
    log.setup(filename=args.logfile)
    logger = logging.getLogger('main')

    try:
        cls = command.import_command(args.command)
        cls(config.Config(args.config)).main()
    except command.CommandException, e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
