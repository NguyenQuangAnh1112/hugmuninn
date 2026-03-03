import asyncio
import os
import threading

import discord
from dotenv import load_dotenv
from langchain_core.tools import tool

from src.utils.exception import he
from src.utils.logger import logger

load_dotenv()


intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
_loop: asyncio.AbstractEventLoop = None  # type: ignore
_ready = threading.Event()


@he
@bot.event
async def on_ready():
    logger.info(f"Discord bot online: {bot.user}")
    _ready.set()


@he
def _run_bot():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(bot.start(str(os.getenv("DISCORD_TOKEN"))))


@he
def start_bot():
    thread = threading.Thread(target=_run_bot, daemon=True)
    thread.start()
    _ready.wait(timeout=30)
    logger.info("Discord bot đã sẵn sàng nhận lệnh")


@he
def _send(coro):

    if _loop is None:
        raise RuntimeError("Bot chưa được khởi động. Gọi start_bot() trước.")

    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=20)


@tool
@he
def send_message(channel_id: str, message: str):
    """
    Gửi tin nhắn vào một channel Discord.
    - channel_id: ID của channel (chuột phải vào channel → Copy ID)
    - message: nội dung tin nhắn
    """

    async def _do():
        raw = await bot.fetch_channel(int(channel_id))

        if raw is None:
            return f"Không tìm thấy channel {channel_id}"

        if not isinstance(
            raw,
            (discord.TextChannel, discord.Thread, discord.DMChannel),
        ):
            return f"Channel {channel_id} không hỗ trợ gửi tin nhắn"

        await raw.send(message)
        return f"Đã gửi tin nhắn vào channel {channel_id}"

    return _send(_do())


@tool
@he
def send_dm(user_id: str, message: str):
    """
    Gửi DM trực tiếp cho người dùng.
    - user_id: ID của user (chuột phải vào user → Copy ID)
    - message: nội dung tin nhắn
    """

    async def _do():
        user = await bot.fetch_user(int(user_id))

        if user is None:
            return f"Không tìm thấy user {user_id}"

        await user.send(message)
        return f"Đã gửi DM cho user {user_id}"

    return _send(_do())
