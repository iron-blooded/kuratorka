import os

try:
    if os.environ["its_host"]:
        from gigs import живем

        живем()
except Exception as e:
    print(e)


import asyncio
import json
import datetime
import re
import io, copy

# import pysftp
import paramiko  # type: ignore
import threading
import logging
import time
import random
import pymorphy2  # type: ignore
from async_lru import alru_cache  # type: ignore
from functools import lru_cache, wraps, cache
from datetime import timedelta
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from time import sleep

configs = {
    "сервер кураторки": 1137004117647171614,  # id сервера кураторки
    "сообщение с реакцией": 1137019048077557781,  # id сообщения, под которое люди должны поставить реакцию якобы для прохождения кураторки
    "канал оповещений": 1137016771455488060,  # id канала, в которое бот будет срать оповещениями
    "сервер ХГ": 612339223294640128,  # id сервера HG
    "роль ожидание кураторки": 1137020285405630517,
    "роль верефицирован": 1137018790035599501,
}


discord_token = os.environ["inviteHG_discord_token"]
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
client = discord.Client(
    intents=intents,
)
tree_commands = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree_commands.sync(guild=discord.Object(id=guild_id))
    await client.wait_until_ready()
    print("Бот запущен!")
    while not client.is_closed():
        await asyncio.sleep(60 * 5)  # раз в # минут


while True:
    client.run(discord_token)
    sleep(5)
