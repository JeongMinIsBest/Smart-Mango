import asyncio

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

from config import FFMPEG_PATH
from utils.state import get_guild_lock, get_music_state, MusicTrack


class MusicCog(commands.Cog):
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

    async def extract_youtube_info(self, query: str):
        ydl_opts = {
            "format": "bestaudio[ext=webm]/bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "default_search": "ytsearch1",
            "extract_flat": False,
            "nocheckcertificate": True,
            "ignoreerrors": False,
        }

        loop = asyncio.get_running_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if "entries" in info and info["entries"]:
                    return info["entries"][0]
                return info

        return await loop.run_in_executor(None, _extract)

    def build_audio_source(self, audio_url: str):
        before_options = (
            "-reconnect 1 "
            "-reconnect_streamed 1 "
            "-reconnect_at_eof 1 "
            "-reconnect_on_network_error 1 "
            "-reconnect_on_http_error 4xx,5xx "
            "-reconnect_delay_max 10"
        )

        source = discord.FFmpegPCMAudio(
            audio_url,
            executable=FFMPEG_PATH,
            before_options=before_options,
            options="-vn"
        )

        return discord.PCMVolumeTransformer(source, volume=1.3)

    async def create_track(self, query: str, requested_by: str | None = None) -> MusicTrack:
        info = await self.extract_youtube_info(query)

        if not info:
            raise RuntimeError("검색 결과를 찾지 못했습니다.")

        audio_url = info.get("url")
        title = info.get("title", "제목 없음")
        webpage_url = info.get("webpage_url")
        thumbnail_url = info.get("thumbnail")

        if not audio_url:
            raise RuntimeError("오디오 URL을 가져오지 못했습니다.")

        return MusicTrack(
            title=title,
            audio_url=audio_url,
            webpage_url=webpage_url,
            requested_by=requested_by,
            thumbnail_url=thumbnail_url,
        )

    def build_now_playing_embed(self, track: MusicTrack) -> discord.Embed:
        embed = discord.Embed(
            title="🎵 현재 재생 중",
            description=f"**{track.title}**",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="요청자",
            value=track.requested_by or "알 수 없음",
            inline=True
        )

        if track.webpage_url:
            embed.add_field(
                name="링크",
                value=f"[바로 가기]({track.webpage_url})",
                inline=True
            )

        if track.thumbnail_url:
            embed.set_thumbnail(url=track.thumbnail_url)

        embed.set_footer(text="Smart Mango Music")
        return embed

    def build_queue_embed(self, state) -> discord.Embed:
        embed = discord.Embed(
            title="📜 재생목록",
            color=discord.Color.blue()
        )

        if state.current:
            current_text = f"**{state.current.title}**"
            if state.current.requested_by:
                current_text += f"\n요청자: {state.current.requested_by}"
            if state.current.webpage_url:
                current_text += f"\n[링크 열기]({state.current.webpage_url})"

            embed.add_field(
                name="▶️ 현재 재생 중",
                value=current_text,
                inline=False
            )

            if state.current.thumbnail_url:
                embed.set_thumbnail(url=state.current.thumbnail_url)
        else:
            embed.add_field(
                name="▶️ 현재 재생 중",
                value="없음",
                inline=False
            )

        if state.queue:
            queue_lines = []
            for idx, track in enumerate(state.queue[:10], start=1):
                line = f"`{idx}.` {track.title}"
                if track.requested_by:
                    line += f" — {track.requested_by}"
                queue_lines.append(line)

            queue_text = "\n".join(queue_lines)

            if len(state.queue) > 10:
                queue_text += f"\n... 외 {len(state.queue) - 10}곡 더 있어요."

            embed.add_field(
                name=f"🎶 대기열 ({len(state.queue)}곡)",
                value=queue_text,
                inline=False
            )
        else:
            embed.add_field(
                name="🎶 대기열",
                value="비어 있어요.",
                inline=False
            )

        embed.set_footer(text="Smart Mango Music Queue")
        return embed

    def build_start_embed(self, track: MusicTrack) -> discord.Embed:
        embed = discord.Embed(
            title="🎶 재생 시작",
            description=f"**{track.title}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="요청자",
            value=track.requested_by or "알 수 없음",
            inline=True
        )

        if track.webpage_url:
            embed.add_field(
                name="링크",
                value=f"[바로 가기]({track.webpage_url})",
                inline=True
            )

        if track.thumbnail_url:
            embed.set_thumbnail(url=track.thumbnail_url)

        embed.set_footer(text="Smart Mango Music")
        return embed

    async def play_next(self, guild: discord.Guild):
        if guild is None:
            return

        state = get_music_state(guild.id)
        voice_client = guild.voice_client

        if not voice_client or not voice_client.is_connected():
            state.current = None
            state.is_processing = False
            return

        if not state.queue:
            state.current = None
            state.is_processing = False
            return

        next_track = state.queue.pop(0)
        state.current = next_track
        state.is_processing = True

        source = self.build_audio_source(next_track.audio_url)

        channel = None
        if state.text_channel_id:
            channel = guild.get_channel(state.text_channel_id)

        def after_play(error):
            if error:
                print(f"[음악 재생 오류] {error}")
            else:
                print(f"[음악 재생 종료] {next_track.title}")

            future = asyncio.run_coroutine_threadsafe(
                self.after_track_end(guild, next_track, error),
                self.bot.loop
            )

            try:
                future.result()
            except Exception as e:
                print(f"[after_play 후처리 오류] {e}")

        print(f"[음악 재생 시작] {next_track.title}")
        voice_client.play(source, after=after_play)

        if channel:
            try:
                embed = self.build_start_embed(next_track)
                asyncio.create_task(channel.send(embed=embed))
            except Exception as e:
                print(f"[재생 시작 메시지 오류] {e}")

    async def after_track_end(self, guild: discord.Guild, finished_track: MusicTrack, error=None):
        state = get_music_state(guild.id)

        if state.current and state.current.title == finished_track.title:
            state.current = None

        await self.play_next(guild)

    async def maybe_start_playback(self, guild: discord.Guild):
        state = get_music_state(guild.id)
        voice_client = guild.voice_client

        if not voice_client or not voice_client.is_connected():
            return

        if voice_client.is_playing() or voice_client.is_paused():
            return

        if state.current is not None:
            return

        await self.play_next(guild)

    @app_commands.command(
        name="음악",
        description="유튜브에서 음악을 검색해 대기열에 추가하고 자동으로 재생합니다."
    )
    @app_commands.describe(title="재생할 음악 제목")
    async def music(self, interaction: discord.Interaction, title: str):
        query = title.strip()
        if not query:
            await interaction.response.send_message("제목을 입력해 주세요.", ephemeral=True)
            return

        await interaction.response.defer()

        voice_client = await self.ensure_voice(interaction)
        if voice_client is None:
            return

        state = get_music_state(interaction.guild.id)
        state.text_channel_id = interaction.channel_id

        requested_by = (
            interaction.user.display_name
            if isinstance(interaction.user, discord.Member)
            else interaction.user.name
        )

        lock = get_guild_lock(interaction.guild.id)
        async with lock:
            track = await self.create_track(query, requested_by=requested_by)
            state.queue.append(track)

            position = len(state.queue)
            should_start_now = (
                state.current is None
                and not voice_client.is_playing()
                and not voice_client.is_paused()
            )

            if should_start_now:
                embed = discord.Embed(
                    title="🎶 대기열 추가",
                    description=f"**{track.title}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="상태", value="바로 재생할게요.", inline=True)
                embed.add_field(name="요청자", value=requested_by, inline=True)
                if track.thumbnail_url:
                    embed.set_thumbnail(url=track.thumbnail_url)
                embed.set_footer(text="Smart Mango Music")

                await interaction.followup.send(embed=embed)
                await self.maybe_start_playback(interaction.guild)
            else:
                embed = discord.Embed(
                    title="🎶 대기열 추가",
                    description=f"**{track.title}**",
                    color=discord.Color.orange()
                )
                embed.add_field(name="대기열 위치", value=str(position), inline=True)
                embed.add_field(name="요청자", value=requested_by, inline=True)
                if track.thumbnail_url:
                    embed.set_thumbnail(url=track.thumbnail_url)
                embed.set_footer(text="Smart Mango Music Queue")

                await interaction.followup.send(embed=embed)

    @app_commands.command(name="스킵", description="현재 곡을 건너뛰고 다음 곡을 재생합니다.")
    async def skip_music(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.response.send_message("현재 재생 중인 음악이 없어요.", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        state = get_music_state(interaction.guild.id)

        if vc.is_playing() or vc.is_paused():
            skipped_title = state.current.title if state.current else "현재 곡"

            embed = discord.Embed(
                title="⏭ 스킵",
                description=f"**{skipped_title}** 을(를) 스킵했어요.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Smart Mango Music")

            vc.stop()
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("현재 재생 중인 음악이 없어요.", ephemeral=True)

    @app_commands.command(name="정지", description="현재 음악과 대기열을 모두 정지/초기화합니다.")
    async def stop_music(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.response.send_message("현재 재생 중인 음악이 없어요.", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        state = get_music_state(interaction.guild.id)

        state.queue.clear()
        state.current = None
        state.is_processing = False

        if vc.is_playing() or vc.is_paused():
            vc.stop()

        embed = discord.Embed(
            title="⏹ 재생 정지",
            description="음악 재생을 멈추고 대기열도 모두 비웠어요.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Smart Mango Music")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="일시정지", description="현재 재생 중인 음악을 일시정지합니다.")
    async def pause_music(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.response.send_message("현재 재생 중인 음악이 없어요.", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if vc.is_playing():
            vc.pause()

            embed = discord.Embed(
                title="⏸ 일시정지",
                description="현재 음악을 일시정지했어요.",
                color=discord.Color.gold()
            )
            embed.set_footer(text="Smart Mango Music")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("현재 재생 중인 음악이 없어요.", ephemeral=True)

    @app_commands.command(name="다시재생", description="일시정지된 음악을 다시 재생합니다.")
    async def resume_music(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.response.send_message("현재 재생 중인 음악이 없어요.", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if vc.is_paused():
            vc.resume()

            embed = discord.Embed(
                title="▶️ 다시 재생",
                description="일시정지된 음악을 다시 재생했어요.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Smart Mango Music")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("현재 일시정지된 음악이 없어요.", ephemeral=True)

    @app_commands.command(name="현재곡", description="현재 재생 중인 곡을 확인합니다.")
    async def now_playing(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        state = get_music_state(interaction.guild.id)

        if not state.current:
            embed = discord.Embed(
                title="🎵 현재 재생 중인 곡",
                description="현재 재생 중인 곡이 없어요.",
                color=discord.Color.light_grey()
            )
            embed.set_footer(text="Smart Mango Music")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = self.build_now_playing_embed(state.current)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="재생목록", description="현재 대기열을 확인합니다.")
    async def queue_list(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        state = get_music_state(interaction.guild.id)

        if not state.current and not state.queue:
            embed = discord.Embed(
                title="📜 재생목록",
                description="현재 재생 중인 곡과 대기열이 없어요.",
                color=discord.Color.light_grey()
            )
            embed.set_footer(text="Smart Mango Music Queue")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = self.build_queue_embed(state)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))