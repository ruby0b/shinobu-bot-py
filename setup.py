from setuptools import setup

setup(
    name='shinobu-bot',
    version='1.0.0',
    packages=['api', 'data', 'extensions', 'utils'],
    scripts=['shinobu-bot.py'],
    python_requires='>=3.9',
    install_requires=[
        'aiohttp[speedups]',
        'discord.py[voice]',
        'fuzzywuzzy[speedup]',
        'feedparser',
        'aiocache',
        'async-property',
    ],
)
