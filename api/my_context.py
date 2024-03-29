import asyncio
from typing import Optional, Union, Sequence, Collection, Mapping, Callable, Awaitable

import nextcord
from nextcord import Color
from nextcord.ext import commands

from api.expected_errors import ExpectedCommandError
from data.CONSTANTS import NO, YES, PRINTER, DOWN, UP
from utils.formatting import paginate


class Context(commands.Context):
    async def send_embed(self, color: Union[Color, int], description: Optional[str] = None,
                         content: Optional[str] = None, **kwargs):
        kwargs.setdefault('description', description)
        if len(kwargs.get('title', ())) > 256:
            raise ValueError('Title must be 256 or fewer in length')
        if len(kwargs.get('description', ())) > 2048:
            raise ValueError('Description must be 2048 or fewer in length')
        return await self.send(content, embed=nextcord.Embed(color=color, **kwargs))

    async def info(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(nextcord.Color.green(), description, content, **kwargs)

    async def warn(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(nextcord.Color.orange(), description, content, **kwargs)

    async def error(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(nextcord.Color.red(), description, content, **kwargs)

    async def confirm(self, msg: nextcord.Message, users: set[nextcord.User] = None, **kwargs) -> bool:
        users = users or set()

        async def yes(reaction: nextcord.Reaction, **_):
            if users.issubset(await reaction.users().flatten()):
                return True

        async def no(**_):
            return False

        return bool(await self.reaction_buttons(msg, {YES: yes, NO: no}, users=users, **kwargs))

    async def reaction_buttons(self, msg: nextcord.Message,
                               reactions: Mapping[str, Callable[..., Awaitable]],
                               *, users: Collection[nextcord.User] = (), timeout: int = 300):
        users = users or [self.author]
        for r in reactions:
            await msg.add_reaction(r)

        def any_user_answered(reaction: nextcord.Reaction, user: nextcord.User) -> bool:
            return (reaction.message.id == msg.id
                    and user in users
                    and str(reaction.emoji) in reactions)

        try:
            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=timeout, check=any_user_answered)
                except asyncio.TimeoutError:
                    break

                if callback := reactions.get(reaction.emoji):
                    try:
                        ret = await callback(reaction=reaction, user=user)

                    except ExpectedCommandError as e:
                        # Handle the exception but continue waiting for more reactions
                        await self.bot.on_command_error(self, e)
                        continue

                    finally:
                        # Remove the user's reaction if possible in case they want to click it again
                        try:
                            await reaction.remove(user)
                        except (nextcord.Forbidden, nextcord.NotFound):
                            pass

                    if ret is not None:
                        return ret

        finally:
            try:
                # Clear the reactions since clicking them no longer does anything
                await msg.clear_reactions()
            except (nextcord.Forbidden, nextcord.NotFound):
                pass

    async def send_paginated(self, content: str, prefix: str = '', suffix: str = '', **kwargs):
        pages = list(paginate(content, prefix=prefix, suffix=suffix))
        await self.send_pager(pages, **kwargs)

    async def send_pager(self, pages: Sequence[str], *, users: Collection[nextcord.User] = (), timeout: int = 600):
        i = 0
        msg = await self.send(pages[i])

        if len(pages) == 1:
            return

        async def update_page(new_number: int):
            nonlocal i
            i = new_number
            await msg.edit(content=pages[i])

        async def printer(**_):
            await msg.delete()
            for p in pages:
                await self.send(p)

        async def up(**_):
            await update_page(max(i - 1, 0))

        async def down(**_):
            await update_page(min(i + 1, len(pages) - 1))

        await self.reaction_buttons(msg, users=users, timeout=timeout,
                                    reactions={UP: up, DOWN: down, PRINTER: printer})

    async def quick_question(self, question: str, user: Optional[nextcord.User] = None, delete_answer: bool = True
                             ) -> Optional[str]:
        user = user or self.author
        question_msg = await self.info(question)

        def check(m: nextcord.Message):
            return m.channel == self.channel and m.author == user

        try:
            answer = await self.bot.wait_for('message', timeout=120, check=check)
        except asyncio.TimeoutError:
            return None
        else:
            content = answer.content
            if delete_answer:
                try:
                    await answer.delete()
                except (nextcord.Forbidden, nextcord.NotFound):
                    pass
            return content
        finally:
            try:
                await question_msg.delete()
            except (nextcord.Forbidden, nextcord.NotFound):
                pass
