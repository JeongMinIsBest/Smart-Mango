import asyncio
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.state import (
    pomodoro_tasks,
    get_pomodoro_config,
    get_pomodoro_status,
)


def format_seconds(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    if s == 0:
        return f"{m}분"
    return f"{m}분 {s}초"


def format_clock(dt: datetime) -> str:
    return f"{dt.hour:02d}시 {dt.minute:02d}분"


def phase_to_korean(phase: str | None) -> str:
    mapping = {
        "work": "집중 시간",
        "short_break": "짧은 휴식",
        "long_break": "긴 휴식",
    }
    return mapping.get(phase, "알 수 없음")


def next_phase_to_korean(phase: str | None) -> str:
    mapping = {
        "work": "공부 시간",
        "short_break": "휴식 시간",
        "long_break": "긴 휴식 시간",
    }
    return mapping.get(phase, "다음 단계")


def remaining_seconds(ends_at: datetime | None) -> int:
    if ends_at is None:
        return 0
    diff = int((ends_at - datetime.now()).total_seconds())
    return max(diff, 0)


class PomodoroCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def wait_with_one_minute_alert(
        self,
        channel: discord.abc.Messageable,
        duration_seconds: int,
        alert_message: str,
    ):
        if duration_seconds > 60:
            await asyncio.sleep(duration_seconds - 60)
            await channel.send(alert_message)
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(duration_seconds)

    async def pomodoro_loop(self, channel: discord.abc.Messageable, guild_id: int):
        config = get_pomodoro_config(guild_id)
        status = get_pomodoro_status(guild_id)

        cycle = 0
        try:
            while True:
                cycle += 1

                work_start = datetime.now()
                work_end = work_start + timedelta(seconds=config.work_seconds)

                next_break_phase = "long_break" if cycle % 4 == 0 else "short_break"

                status.is_running = True
                status.phase = "work"
                status.cycle = cycle
                status.started_at = work_start
                status.ends_at = work_end
                status.next_phase = next_break_phase

                await channel.send(
                    f"🍅 {cycle}번째 집중 시작! {format_seconds(config.work_seconds)} 동안 공부해요. "
                    f"(다음 휴식 시간: {format_clock(work_end)})"
                )

                await self.wait_with_one_minute_alert(
                    channel,
                    config.work_seconds,
                    "⏰ 1분 뒤 휴식 시간이에요!"
                )

                if cycle % 4 == 0:
                    break_start = datetime.now()
                    break_end = break_start + timedelta(seconds=config.long_break_seconds)

                    status.is_running = True
                    status.phase = "long_break"
                    status.started_at = break_start
                    status.ends_at = break_end
                    status.next_phase = "work"

                    await channel.send(
                        f"🛋️ 4세트 완료! 긴 휴식 {format_seconds(config.long_break_seconds)} 시작! "
                        f"(다음 공부 시간: {format_clock(break_end)})"
                    )

                    await self.wait_with_one_minute_alert(
                        channel,
                        config.long_break_seconds,
                        "⏰ 1분 뒤 다시 공부 시간이 시작돼요!"
                    )
                else:
                    break_start = datetime.now()
                    break_end = break_start + timedelta(seconds=config.short_break_seconds)

                    status.is_running = True
                    status.phase = "short_break"
                    status.started_at = break_start
                    status.ends_at = break_end
                    status.next_phase = "work"

                    await channel.send(
                        f"☕ 짧은 휴식 {format_seconds(config.short_break_seconds)} 시작! "
                        f"(다음 공부 시간: {format_clock(break_end)})"
                    )

                    await self.wait_with_one_minute_alert(
                        channel,
                        config.short_break_seconds,
                        "⏰ 1분 뒤 다시 공부 시간이 시작돼요!"
                    )

        except asyncio.CancelledError:
            await channel.send("🍅 뽀모도로를 종료했어요.")
            raise
        finally:
            status.is_running = False
            status.phase = None
            status.cycle = 0
            status.started_at = None
            status.ends_at = None
            status.next_phase = None

            current = pomodoro_tasks.get(guild_id)
            if current is asyncio.current_task():
                pomodoro_tasks.pop(guild_id, None)

    @app_commands.command(
        name="뽀모도로",
        description="집중/휴식을 반복하는 뽀모도로를 시작합니다."
    )
    async def pomodoro_start(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        if interaction.guild.id in pomodoro_tasks:
            await interaction.response.send_message("이미 뽀모도로가 실행 중이에요.", ephemeral=True)
            return

        config = get_pomodoro_config(interaction.guild.id)
        next_break_time = datetime.now() + timedelta(seconds=config.work_seconds)

        task = asyncio.create_task(
            self.pomodoro_loop(interaction.channel, interaction.guild.id)
        )
        pomodoro_tasks[interaction.guild.id] = task

        await interaction.response.send_message(
            f"🍅 뽀모도로를 시작했어요. "
            f"(다음 휴식 시간: {format_clock(next_break_time)})"
        )

    @app_commands.command(
        name="뽀모종료",
        description="현재 실행 중인 뽀모도로를 종료합니다."
    )
    async def pomodoro_stop(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        task = pomodoro_tasks.get(interaction.guild.id)
        if not task:
            await interaction.response.send_message("현재 실행 중인 뽀모도로가 없어요.", ephemeral=True)
            return

        task.cancel()
        await interaction.response.send_message("뽀모도로 종료 요청을 보냈어요.", ephemeral=True)

    @app_commands.command(
        name="뽀모상태",
        description="현재 뽀모도로 상태와 남은 시간을 확인합니다."
    )
    async def pomodoro_status(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        status = get_pomodoro_status(interaction.guild.id)
        config = get_pomodoro_config(interaction.guild.id)

        if not status.is_running or not status.phase or not status.ends_at:
            await interaction.response.send_message(
                "현재 실행 중인 뽀모도로가 없어요.\n"
                f"기본 설정: 집중 {format_seconds(config.work_seconds)}, "
                f"짧은 휴식 {format_seconds(config.short_break_seconds)}, "
                f"긴 휴식 {format_seconds(config.long_break_seconds)}",
                ephemeral=True
            )
            return

        remain = remaining_seconds(status.ends_at)

        message = (
            f"📌 현재 상태: {phase_to_korean(status.phase)}\n"
            f"📚 현재 세트: {status.cycle}번째 세트\n"
            f"⏳ 남은 시간: {format_seconds(remain)}\n"
            f"🕒 다음 전환 시간: {format_clock(status.ends_at)}\n"
            f"➡️ 다음 단계: {next_phase_to_korean(status.next_phase)}"
        )

        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(
        name="뽀모설정",
        description="뽀모도로 시간을 분 단위로 설정합니다."
    )
    @app_commands.describe(
        집중="집중 시간(분)",
        짧은휴식="짧은 휴식 시간(분)",
        긴휴식="긴 휴식 시간(분)"
    )
    async def pomodoro_config_command(
        self,
        interaction: discord.Interaction,
        집중: app_commands.Range[int, 1, 180],
        짧은휴식: app_commands.Range[int, 1, 60],
        긴휴식: app_commands.Range[int, 1, 180],
    ):
        if not interaction.guild:
            await interaction.response.send_message("서버에서만 사용할 수 있어요.", ephemeral=True)
            return

        if interaction.guild.id in pomodoro_tasks:
            await interaction.response.send_message(
                "뽀모도로 실행 중에는 시간을 변경할 수 없어요. 먼저 /뽀모종료 후 다시 설정해 주세요.",
                ephemeral=True
            )
            return

        config = get_pomodoro_config(interaction.guild.id)
        config.work_seconds = 집중 * 60
        config.short_break_seconds = 짧은휴식 * 60
        config.long_break_seconds = 긴휴식 * 60

        await interaction.response.send_message(
            "✅ 뽀모도로 시간이 변경되었어요.\n"
            f"🍅 집중: {집중}분\n"
            f"☕ 짧은 휴식: {짧은휴식}분\n"
            f"🛋️ 긴 휴식: {긴휴식}분"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(PomodoroCog(bot))