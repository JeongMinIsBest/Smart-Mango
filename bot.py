# 봇 실행, cog 로딩, 명령어 동기화, 공통 에러 처리

import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_TOKEN, TEST_GUILD_ID, BOT_STATUS


class StudyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.voice_states = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        extensions = [
            "cogs.clean",
            "cogs.voice",
            "cogs.pomodoro",
            "cogs.music",
            "cogs.help",
        ]

        for extension in extensions:
            await self.load_extension(extension)

        if TEST_GUILD_ID:
            guild = discord.Object(id=TEST_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"테스트 서버 명령어 동기화 완료: {len(synced)}개")
        else:
            synced = await self.tree.sync()
            print(f"전역 명령어 동기화 완료: {len(synced)}개")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name=BOT_STATUS))
        print(f"로그인 완료: {self.user}")


bot = StudyBot()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        message = "이 명령어를 사용할 권한이 없어요."
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = "잠시 후 다시 시도해 주세요."
    elif isinstance(error, app_commands.CheckFailure):
        message = "이 명령어를 사용할 수 없어요."
    else:
        message = "명령어 처리 중 오류가 발생했어요."
        print(f"[APP COMMAND ERROR] {type(error).__name__}: {error}")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception as send_error:
        print(f"[ERROR RESPONSE FAILED] {send_error}")


bot.run(DISCORD_TOKEN)