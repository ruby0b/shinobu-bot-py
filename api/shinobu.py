import logging
import os
import re
import traceback

import discord
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from utils import database

logger = logging.getLogger(__name__)


class Shinobu(commands.Bot):

    EXTENSION_MODULES = ['extensions.' + ext for ext in """
        call_notification economy misc myanimelist shop trade
    """.split()]

    async def on_ready(self):
        self.update_user_database()
        self.reload_all_extensions()
        logger.info(f'Logged on as {self.user}!')

    async def on_member_join(self, _: discord.Member):
        self.update_user_database()

    def update_user_database(self):
        with database.connect() as db:
            db.executemany('INSERT OR IGNORE INTO user(id) VALUES(?)',
                           [[m.id] for g in self.guilds for m in g.members])

    def reload_all_extensions(self):
        for ext in self.EXTENSION_MODULES:
            try:
                self.reload_extension(ext)
            except commands.ExtensionNotLoaded:
                self.load_extension(ext)

    async def on_command_error(self, ctx: Context, exception: Exception):
        if (self.extra_events.get('on_command_error', None)
                or hasattr(ctx.command, 'on_error')
                or (ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error))
                or isinstance(exception, commands.CommandNotFound)):
            return

        if isinstance(exception, commands.CommandInvokeError):
            # "unbox" errors produced while invoking a command
            exception = exception.original

        if isinstance(exception, ExpectedCommandError):
            # if the error was expected then simply send the exception message to the user
            await ctx.error(exception.message)
        else:
            await ctx.error(re.sub(r'.*?(\w+?:.*)',
                                   repl=lambda m: m.group(1),
                                   string=traceback.format_exception_only(type(exception), exception)[-1]))
            logger.info(f'Ignoring exception in command {ctx.command}:\n'
                        + ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

    async def get_context(self, message, *, cls=Context):
        # inject our own Context data type
        return await super().get_context(message, cls=cls)
