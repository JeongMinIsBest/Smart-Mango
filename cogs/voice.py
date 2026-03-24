# TTS 입장/퇴장, 읽기 기능

import os
import asyncio
import tempfile

import discord
from discord import app_commands
from discord.ext import commands
from gtts import gTTS

from config import FFMPEG_PATH
from utils.state import TTSState, tts_states


class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def ensure_voice(self, interaction: discord.Interaction) -> discord.VoiceClient | None:
        if not interaction.guild or not interaction.user:
            return None

        if not isinstance(interaction.user, discord.Member):
            return None

        if not interaction.user.voice or not interaction.user.voice.channel:
            if interaction.response.is_done():
                await interaction.followup.send("먼저 음성 채널에 들어가 주세요.", ephemeral=True)
            else:
                await interaction.response.send_message("먼저 음성 채널에 들어가 주세요.", ephemeral=True)
            return None

        target_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected():
            if voice_client.channel != target_channel:
                await voice_client.move_to(target_channel)
            return voice_client

        return await target_channel.connect()

    async def speak_text(self, voice_client: discord.VoiceClient, text: str, lang: str = "ko"):
        if not text.strip():
            return

        loop = asyncio.get_running_loop()

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            temp_path = tmp.name

        def _make_tts():
            tts = gTTS(text=text, lang=lang)
            tts.save(temp_path)

        await loop.run_in_executor(None, _make_tts)

        while voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(0.3)

        finished = asyncio.Event()

        def after_play(error):
            if error:
                print(f"[TTS 재생 오류] {error}")
            try:
                os.remove(temp_path)
            except OSError:
                pass
            loop.call_soon_threadsafe(finished.set)

        source = discord.FFmpegPCMAudio(temp_path, executable=FFMPEG_PATH)
        voice_client.play(source, after=after_play)
        await finished.wait()

    @app_commands.command(name="입장", description="음성 채널에 입장하고 현재 채널 TTS를 활성화합니다.")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        voice_client = await self.ensure_voice(interaction)
        if voice_client is None:
            return

        tts_states[interaction.guild.id] = TTSState(
            enabled=True,
            text_channel_id=interaction.channel_id
        )

        await interaction.followup.send(
            "음성 채널에 입장했고, 현재 텍스트 채널의 메시지를 읽도록 설정했어요.",
            ephemeral=True
        )

    @app_commands.command(name="퇴장", description="음성 채널에서 나가고 TTS를 비활성화합니다.")
    async def leave(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        voice_client = interaction.guild.voice_client

        if interaction.guild.id in tts_states:
            tts_states[interaction.guild.id].enabled = False

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

        await interaction.response.send_message("음성 채널에서 나가고 TTS를 종료했어요.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        state = tts_states.get(message.guild.id)
        if not state or not state.enabled:
            return

        if state.text_channel_id != message.channel.id:
            return

        voice_client = message.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            return

        if voice_client.is_playing():
            return

        text = message.content.strip()
        if not text:
            return

        try:
            await self.speak_text(voice_client, text, lang="ko")
        except Exception as e:
            print(f"[TTS 오류] {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceCog(bot))