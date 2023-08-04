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

config = {
    "сервер кураторки": 1137004117647171614,  # id сервера кураторки
    "сообщение с реакцией": 1137019048077557781,  # id сообщения, под которое люди должны поставить реакцию якобы для прохождения кураторки
    "канал оповещений": 1137016771455488060,  # id канала, в которое бот будет срать оповещениями
    "сервер ХГ": 612339223294640128,  # id сервера HG
    "роль ожидание кураторки": 1137020285405630517,
    "роль верефицирован": 1137018790035599501,
    "роль участник": 612341683014598656,
}


discord_token = os.environ["inviteHG_discord_token"]
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
client = discord.Client(
    intents=intents,
)


def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.datetime.utcnow() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


@client.event
async def on_ready():
    await client.wait_until_ready()
    print("Бот запущен!")
    while not client.is_closed():
        await asyncio.sleep(60 * 5)  # раз в # минут


@client.event
async def on_member_join(member: discord.Member):
    if member.guild.id == config["сервер ХГ"] and config["роль верефицирован"] in [
        role.id
        for role in get_guild(config["сервер кураторки"]).get_member(member.id).roles
    ]:
        member.add_roles(
            get_role(config["сервер ХГ"], config["роль участник"]),
            reason="Bерефицирован в кураторке",
        )
        get_guild(config["сервер кураторки"]).kick(
            member, reason="Прошел кураторку и зашел на сервер ХГ"
        )
        return


@timed_lru_cache(300)
def get_guild(id: int) -> discord.Guild:
    global client
    return client.get_guild(id)


@timed_lru_cache(300)
def get_role(guild: int, role: int) -> discord.Role:
    return get_guild(guild).get_role(role)


while True:
    client.run(discord_token)
    sleep(5)
