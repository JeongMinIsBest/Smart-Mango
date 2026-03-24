import asyncio
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TTSState:
    enabled: bool = False
    text_channel_id: int | None = None


@dataclass
class PomodoroConfig:
    work_seconds: int = 25 * 60
    short_break_seconds: int = 5 * 60
    long_break_seconds: int = 30 * 60


@dataclass
class PomodoroStatus:
    is_running: bool = False
    phase: str | None = None
    cycle: int = 0
    started_at: datetime | None = None
    ends_at: datetime | None = None
    next_phase: str | None = None


@dataclass
class MusicTrack:
    title: str
    audio_url: str
    webpage_url: str | None = None
    requested_by: str | None = None
    thumbnail_url: str | None = None


@dataclass
class MusicState:
    queue: list[MusicTrack] = field(default_factory=list)
    current: MusicTrack | None = None
    is_processing: bool = False
    text_channel_id: int | None = None


tts_states: dict[int, TTSState] = {}
pomodoro_tasks: dict[int, asyncio.Task] = {}
music_locks: dict[int, asyncio.Lock] = {}

pomodoro_configs: dict[int, PomodoroConfig] = {}
pomodoro_statuses: dict[int, PomodoroStatus] = {}
music_states: dict[int, MusicState] = {}


def get_guild_lock(guild_id: int) -> asyncio.Lock:
    if guild_id not in music_locks:
        music_locks[guild_id] = asyncio.Lock()
    return music_locks[guild_id]


def get_pomodoro_config(guild_id: int) -> PomodoroConfig:
    if guild_id not in pomodoro_configs:
        pomodoro_configs[guild_id] = PomodoroConfig()
    return pomodoro_configs[guild_id]


def get_pomodoro_status(guild_id: int) -> PomodoroStatus:
    if guild_id not in pomodoro_statuses:
        pomodoro_statuses[guild_id] = PomodoroStatus()
    return pomodoro_statuses[guild_id]


def get_music_state(guild_id: int) -> MusicState:
    if guild_id not in music_states:
        music_states[guild_id] = MusicState()
    return music_states[guild_id]