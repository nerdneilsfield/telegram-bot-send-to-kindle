#!/bin/env python3

import sys
from toml import loads

from KindleBot.bot import Bot

def help():
    print("""
Kindle Bot Usage:

python3 app.py -c config.toml

""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        help()
    elif sys.argv[1] != "-c":
        help()
    else:
        configs = loads(open(sys.argv[2], 'r').read())
        bot = Bot(configs)
        bot.start()
