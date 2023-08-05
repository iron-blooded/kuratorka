#!/usr/bin/env python3

import os

try:
    if os.environ["its_host"]:
        from gigs import живем

        живем()
except Exception as e:
    print(e)


import asyncio
import datetime
import random

from async_lru import alru_cache  # type: ignore
from functools import lru_cache, wraps
from datetime import timedelta
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from time import sleep


class config:
    server_kuratorka = 1137004117647171614 
    '''id сервера кураторки'''
    message_reacting = 1137019048077557781
    '''id сообщения, под которое люди должны поставить реакцию якобы для прохождения кураторки'''
    channel_alert = 1137016771455488060
    '''id канала, в которое бот будет срать оповещениями'''
    server_HG = 612339223294640128
    """id сервера HG"""
    role_wait_kurator = 1137020285405630517
    """роль ожидание кураторки"""
    role_vereficate = 1137018790035599501
    """роль верефицирован"""
    role_participant = 612341683014598656
    """роль участник"""
    channel_writing_anketa = 1137358502239682712
    """канал с написанием анкет"""
    role_curator = 1137018745567584326
    """куратор"""

    def __init__(self) -> None:
        pass


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
    if member.guild.id == config.server_HG and config.role_vereficate in [
        role.id
        for role in get_guild(config.server_kuratorka).get_member(member.id).roles
    ]:  # если чел заходит на ХГ, и он верефицирован
        await member.add_roles(
            get_role(config.server_HG, config.role_participant),
            reason="Bерефицирован в кураторке",
        )
        await get_guild(config.server_kuratorka).kick(
            member, reason="Прошел кураторку и зашел на сервер ХГ"
        )
        return


@client.event
async def on_message(message: discord.Message):
    if message.channel.id == config.channel_writing_anketa:
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        return


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    user = payload.member
    if user.id == client.user.id:
        return
    emoji = payload.emoji
    message_reacted = await client.get_channel(payload.channel_id).fetch_message(
        payload.message_id
    )
    if (
        payload.message_id == config.message_reacting
    ):  # если реакцию поставили под сообщение с запросом кураторки
        await user.add_roles(
            get_role(config.server_kuratorka, config.role_wait_kurator),
            reason="Запросил кураторку",
        )
        await message_reacted.remove_reaction(payload.emoji, user)
        channel = client.get_channel(config.channel_alert)
        message = await channel.send(
            f"""@here <@{user.id}> желает пройти кураторку!\nЕсли игрок прошел кураторку, ставьте галочку, но если он на 24% умнее собаки - крестик.""",
            tts=True,
        )
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        return
    if (
        payload.channel_id == config.channel_alert
    ):  # если канал - канал с алертами кураторов
        user_wait_kuratorka = None
        for user_reacted in message_reacted.mentions:
            user_wait_kuratorka = user_reacted
        if emoji.name == "✅":
            await message_reacted.edit(
                content=f"✅ Пользователь <@{user_wait_kuratorka.id}> успешно прошел кураторку.\nПодтвердил: <@{user.id}>"
            )
            await user_wait_kuratorka.remove_roles(
                get_role(config.server_kuratorka, config.role_wait_kurator),
                reason="Прошел кураторку",
            )
            await user_wait_kuratorka.add_roles(
                get_role(config.server_kuratorka, config.role_vereficate),
                reason="Прошел кураторку",
            )
        else:
            await message_reacted.edit(
                content=f"❌ <@{user_wait_kuratorka.id}> сообщил что в курсе, как работает этот станок 1939 года выпуска.\nПодтвердил: <@{user.id}>"
            )
            await user_wait_kuratorka.ban(
                reason=f"Претензии к прохождению кураторки от {user.id}."
            )
        await message_reacted.clear_reactions()
        return
    if (
        payload.channel_id == config.channel_writing_anketa
    ):  # если канал - канал с анкетами
        if config.role_curator not in [i.id for i in user.roles]:
            await message_reacted.remove_reaction(payload.emoji, user)
            return
        if emoji.name == "✅":
            channel = client.get_channel(config.channel_alert)
            message = await channel.send(
                f"""✅ Пользователь <@{message_reacted.author.id}> успешно прошел кураторку написав анкету.\nПодтвердил: <@{user.id}>""",
                tts=True,
            )
            await message_reacted.author.remove_roles(
                get_role(config.server_kuratorka, config.role_wait_kurator),
                reason="Анкета принята",
            )
            await message_reacted.author.add_roles(
                get_role(config.server_kuratorka, config.role_vereficate),
                reason="Анкета принята",
            )
            return


async def play_music(voice_channel: discord.VoiceChannel):
    def get_files_in_directory(directory_path):
        file_list = []
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                file_list.append(filename)
        return file_list

    voice_client = await voice_channel.connect()
    try:
        while voice_client.is_connected:
            music = get_files_in_directory("music")
            random.shuffle(music)
            await voice_client.play(
                discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("music/" + music[-1]), volume=0.1),
                after=lambda e: voice_client.disconnect(),
            )
    except Exception as e:
        print(e)
    # await voice_client.disconnect()


@client.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if member.bot or member.guild.id == config.server_HG:
        return
    if before.channel != after.channel:
        voice_channel = after.channel
        if client.voice_clients:
            for voice_client in client.voice_clients:
                if voice_client.guild == member.guild:
                    # Если бот уже в голосовом канале на этом сервере, выходим из него
                    await voice_client.disconnect()
        if voice_channel is not None and not client.voice_clients:
            count = 0
            for user in after.channel.members:
                if not user.bot:
                    count += 1
            if count <= 1:
                try:
                    await play_music(voice_channel)
                except discord.errors.ClientException:
                    print("Бот уже находится в голосовом канале.")
            else:
                await voice_client.disconnect()


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
