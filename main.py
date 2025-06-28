#!/usr/bin/env python3

import os


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
    server_kuratorka = 1217209541197041714
    """id сервера кураторки"""
    message_reacting = 1311010717700456468
    """id сообщения, под которое люди должны поставить реакцию якобы для прохождения кураторки"""
    channel_alert = 1311008897988952074
    """id канала, в которое бот будет срать оповещениями"""
    server_HG = 612339223294640128
    """id сервера HG"""
    role_wait_kurator = 1385299820582801499
    """роль ожидание кураторки"""
    role_vereficate = 1385300015261552791
    """роль верефицирован"""
    role_participant = 612341683014598656
    """роль участник на ХГ"""
    role_unvereficate = 1050035683848364064
    """роль неверефицирован на ХГ"""
    channel_writing_anketa = 1353112568595742740
    """канал с написанием анкет"""
    role_curator = 1217209541197041717
    """роль куратор"""
    role_confirm_ticket = 1385298742701199422
    """роль о одобрении тикета"""

    def __init__(self) -> None:
        pass


discord_token = os.environ["inviteHG_discord_token"]
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
if "proxy_http" in os.environ:
    client = discord.Client(intents=intents, proxy=os.environ["proxy_http"])
else:
    client = discord.Client(
        intents=intents,
    )
tree_commands = app_commands.CommandTree(client)

requested_curator: set = (
    set()
)  # Список id юзеров, что запросили кураторку. Что бы не спамили


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


async def vereficate_and_kick(member: discord.Member):
    global requested_curator
    requested_curator.remove(member.id)
    member = get_guild(config.server_HG).get_member(member.id)
    await member.add_roles(
        get_role(config.server_HG, config.role_participant),
        reason="Bерефицирован в кураторке",
    )
    await member.remove_roles(
        get_role(config.server_HG, config.role_unvereficate),
        reason="Bерефицирован в кураторке",
    )
    await member.edit(
        nick=get_guild(config.server_kuratorka).get_member(member.id).display_name,
        reason="Bерефицирован в кураторке",
    )
    await get_guild(config.server_kuratorka).kick(
        member, reason="Прошел кураторку и зашел на сервер ХГ"
    )
    return


@client.event
async def on_ready():
    await tree_commands.sync()
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
        await asyncio.sleep(2)
        return await vereficate_and_kick(member)


@client.event
async def on_message(message: discord.Message):
    if (
        message.channel.id == config.channel_writing_anketa
        and message.author.id != config.role_curator
    ):
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        return


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    global requested_curator
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
        if user.id in requested_curator:
            return  # Что бы не было повторок в уведомлениях
        channel_alert = client.get_channel(config.channel_alert)
        message = await channel_alert.send(
            (
                f"""@here <@&{config.role_curator}> """
                if user.id != 1129473387220176968
                else ""
            )
            + f"""<@{user.id}> желает пройти кураторку!\nЕсли игрок прошел кураторку, ставьте галочку, но если он всего лишь на 24% умнее собаки - крестик.""",
            tts=True,
        )
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        requested_curator.add(user.id)
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
            if get_guild(config.server_HG).get_member(user_wait_kuratorka.id):
                await vereficate_and_kick(user_wait_kuratorka)
            else:
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
            await get_guild(config.server_kuratorka).ban(
                user_wait_kuratorka,
                reason=f"Претензии к прохождению кураторки от {user.id}.",
            )
        requested_curator.remove(user_wait_kuratorka.id)
        await message_reacted.clear_reactions()
        return
    if (
        payload.channel_id == config.channel_writing_anketa
    ):  # если канал - канал с анкетами
        if not user.roles or config.role_curator not in [i.id for i in user.roles]:
            await message_reacted.remove_reaction(payload.emoji, user)
            return
        channel_alert = client.get_channel(config.channel_alert)
        if emoji.name == "❌":
            await message_reacted.remove_reaction("✅", client.user)
        elif emoji.name == "✅":  # одобрение тикета
            message = await channel_alert.send(
                f"""✅ <@{user.id}> по результатам анкеты подтвердил адекватность пользователя <@{message_reacted.author.id}>\nПосле проведения Кураторки вы можете подтвердить ее успех, нажав реакцию 🎉 в канале https://discord.com/channels/{config.server_kuratorka}/{config.channel_writing_anketa}/{message_reacted.id}""",
            )
            await message_reacted.author.add_roles(
                get_role(config.server_kuratorka, config.role_confirm_ticket),
                reason="Анкета принята",
            )
            await message_reacted.clear_reactions()
            await message_reacted.add_reaction("🎉")
        elif emoji.name == "🎉":  # завершение кураторки
            message = await channel_alert.send(
                f"""🎉 Пользователь <@{message_reacted.author.id}> успешно прошел кураторку на основе анкеты.\nПодтвердил: <@{user.id}>""",
            )
            await message_reacted.author.remove_roles(
                get_role(config.server_kuratorka, config.role_wait_kurator),
                reason="Кураторка на основе анкеты проведена проведена",
            )
            await message_reacted.author.remove_roles(
                get_role(config.server_kuratorka, config.role_confirm_ticket),
                reason="Кураторка на основе анкеты проведена проведена",
            )
            await message_reacted.author.add_roles(
                get_role(config.server_kuratorka, config.role_vereficate),
                reason="Кураторка на основе анкеты проведена проведена",
            )
            return


async def play_music(
    voice_channel: discord.VoiceChannel, special: bool, list_file_path: str = "list.txt"
):
    def get_urls_from_file(file_path):
        with open(file_path, "r") as file:
            urls = [url.strip() for url in file.readlines() if url.strip()]
        return urls

    if client.voice_clients:
        for voice_client in client.voice_clients:
            if voice_client.channel.guild is voice_channel.guild:
                await voice_client.disconnect()
    voice_client = await voice_channel.connect()
    try:
        urls = get_urls_from_file(list_file_path)
        random.shuffle(urls)
        for url in urls:
            voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        "https://5.restream.one/1465_1",
                        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                        options="-af 'volume=0.1'",
                    ),
                    volume=0.1,
                )
            )
            while voice_client.is_playing():
                await asyncio.sleep(1)
                if (
                    not voice_client.is_connected()
                    or (not special and len(voice_channel.members) > 2)
                    or len(voice_channel.members) < 2
                ):
                    break
    except Exception as e:
        print(e)
    finally:
        await voice_client.disconnect(force=True)


# @client.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if "proxy_http" in os.environ:
        return
    if before.channel != after.channel:
        voice_channel = after.channel
        if voice_channel is not None:
            count = 0
            for user in after.channel.members:
                if not user.bot:
                    count += 1
            if count <= 1:
                try:
                    if (
                        member.guild.id != config.server_HG
                        or "Основа" in voice_channel.name
                        or "Кураторка" in voice_channel.name
                    ):
                        return await play_music(voice_channel, False)
                except discord.errors.ClientException as e:
                    print(f"Бот уже находится в голосовом канале: {e}")
            # else:
            # return await voice_client.disconnect()


@tree_commands.command(
    name="join_in_channel",
    description="Подключается к голосовому каналу и играет музыку",
)
async def join_in_channel(
    interaction: discord.Interaction, channel: discord.VoiceChannel
):
    await interaction.response.defer(ephemeral=True)
    await play_music(channel, True)
    return await interaction.followup.send("Успешно")


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
