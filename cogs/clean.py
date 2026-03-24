import discord
from discord import app_commands
from discord.ext import commands


class CleanCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="청소", description="현재 시점 이전의 채널 메시지를 정리합니다.")
    async def clean(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("텍스트 채널에서만 사용할 수 있어요.", ephemeral=True)
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("서버 멤버만 사용할 수 있어요.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("메시지 관리 권한이 필요합니다.", ephemeral=True)
            return

        bot_member = interaction.guild.me
        if bot_member is None or not bot_member.guild_permissions.manage_messages:
            await interaction.response.send_message("봇에 메시지 관리 권한이 필요합니다.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        deleted_count = 0

        try:
            # interaction.created_at 이전 메시지들을 전부 순회하면서 삭제
            async for message in channel.history(limit=None, before=interaction.created_at, oldest_first=False):
                try:
                    await message.delete()
                    deleted_count += 1
                except discord.Forbidden:
                    await interaction.followup.send(
                        "일부 메시지를 삭제할 권한이 없어요.",
                        ephemeral=True
                    )
                    return
                except discord.HTTPException:
                    # 너무 오래된 메시지거나 기타 API 문제일 수 있으니 건너뜀
                    continue

            await interaction.followup.send(
                f"🧹 현재 시점 이전 메시지 {deleted_count}개를 삭제했어요.",
                ephemeral=False
            )

        except Exception as e:
            await interaction.followup.send(
                f"청소 중 오류가 발생했어요: {e}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(CleanCog(bot))