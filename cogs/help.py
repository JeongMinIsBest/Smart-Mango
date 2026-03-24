import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_help_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📖 Smart Mango 도움말",
            description="사용 가능한 명령어 목록이에요.",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🧹 청소",
            value=(
                "`/청소`\n"
                "현재 시점 이전의 채널 메시지를 정리합니다."
            ),
            inline=False
        )

        embed.add_field(
            name="🔊 음성 / TTS",
            value=(
                "`/입장`\n"
                "봇이 음성 채널에 입장하고 현재 채널 TTS를 활성화합니다.\n\n"
                "`/퇴장`\n"
                "봇이 음성 채널에서 나가고 TTS를 종료합니다."
            ),
            inline=False
        )

        embed.add_field(
            name="🍅 뽀모도로",
            value=(
                "`/뽀모도로`\n"
                "뽀모도로를 시작합니다.\n\n"
                "`/뽀모종료`\n"
                "현재 실행 중인 뽀모도로를 종료합니다.\n\n"
                "`/뽀모상태`\n"
                "현재 집중/휴식 상태와 남은 시간을 확인합니다.\n\n"
                "`/뽀모시간설정 집중:분 짧은휴식:분 긴휴식:분`\n"
                "뽀모도로 시간을 직접 설정합니다."
            ),
            inline=False
        )

        embed.add_field(
            name="🎵 음악",
            value=(
                "`/음악 제목:곡이름`\n"
                "유튜브에서 음악을 검색해 대기열에 추가합니다.\n\n"
                "`/현재곡`\n"
                "현재 재생 중인 곡을 확인합니다.\n\n"
                "`/재생목록`\n"
                "현재 대기열을 확인합니다.\n\n"
                "`/스킵`\n"
                "현재 곡을 건너뛰고 다음 곡을 재생합니다.\n\n"
                "`/일시정지`\n"
                "현재 곡을 일시정지합니다.\n\n"
                "`/다시재생`\n"
                "일시정지된 곡을 다시 재생합니다.\n\n"
                "`/정지`\n"
                "현재 곡과 대기열을 모두 정지/초기화합니다."
            ),
            inline=False
        )

        embed.set_footer(text="Smart Mango Bot Help")
        return embed

    @app_commands.command(name="도움말", description="사용 가능한 모든 명령어 설명을 보여줍니다.")
    async def help_command(self, interaction: discord.Interaction):
        embed = self.build_help_embed()

        # 먼저 본인에게 DM 시도
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                "📬 도움말을 DM으로 보내드렸어요!",
                ephemeral=True
            )
        except discord.Forbidden:
            # DM이 막혀 있으면 서버에서 본인만 보이게 전송
            await interaction.response.send_message(
                "DM을 보낼 수 없어서 여기에서 보여드릴게요.",
                embed=embed,
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))