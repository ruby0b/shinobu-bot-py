#!/usr/bin/env python
import nextcord

from data import CONSTANTS
from api.shinobu import Shinobu
from utils.setup_logging import setup_logging


def main():
    setup_logging()

    intents = nextcord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = Shinobu(command_prefix=CONSTANTS.CMD_PREFIX, intents=intents)

    with open('data/TOKEN') as f:
        token = f.readline().strip()
    bot.run(token)

if __name__ == '__main__':
    main()
