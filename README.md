<div align="center">

# 🥭 Smart Mango - 똑똑한 망고

**So helpful, So Kind! It's Smart Mango 🥭**

공부 서버를 위한 올인원 디스코드 봇 — 음악, TTS, 뽀모도로, 채널 청소까지!

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?style=flat-square&logo=discord&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

</div>

---

## ✨ 기능 소개

| 카테고리 | 기능 |
|---------|------|
| 🎵 음악 | 유튜브 검색 재생, 대기열 관리, 스킵/정지/일시정지 |
| 🔊 TTS | 음성 채널 입장 후 채팅 메시지를 자동으로 읽어줌 |
| 🍅 뽀모도로 | 집중/휴식 타이머, 4세트마다 긴 휴식, 1분 전 알림 |
| 🧹 청소 | 텍스트 채널의 이전 메시지 일괄 삭제 |
<br/>

## 🤖 명령어 목록

### 🎵 음악

| 명령어 | 설명 |
|--------|------|
| `/음악 [제목]` | 유튜브에서 검색해 대기열에 추가하고 자동 재생 |
| `/스킵` | 현재 곡을 건너뛰고 다음 곡 재생 |
| `/정지` | 재생을 멈추고 대기열 초기화 |
| `/일시정지` | 현재 재생 일시정지 |
| `/다시재생` | 일시정지된 곡을 다시 재생 |
| `/현재곡` | 현재 재생 중인 곡 정보 확인 |
| `/재생목록` | 대기열 전체 보기 |

### 🔊 TTS (Text-to-Speech)

| 명령어 | 설명 |
|--------|------|
| `/입장` | 음성 채널 입장 & 현재 텍스트 채널 TTS 활성화 |
| `/퇴장` | 음성 채널 퇴장 & TTS 비활성화 |

> TTS가 활성화되면 해당 채널에 입력된 메시지를 봇이 자동으로 읽어줍니다.

### 🍅 뽀모도로

| 명령어 | 설명 |
|--------|------|
| `/뽀모도로` | 뽀모도로 타이머 시작 |
| `/뽀모종료` | 실행 중인 뽀모도로 종료 |
| `/뽀모상태` | 현재 단계, 남은 시간, 다음 전환 시각 확인 |
| `/뽀모설정 [집중] [짧은휴식] [긴휴식]` | 타이머 시간 커스텀 (분 단위) |

**기본 설정**
- 🍅 집중: **25분**
- ☕ 짧은 휴식: **5분**
- 🛋️ 긴 휴식: **30분** (4세트마다)
- ⏰ 각 단계 종료 **1분 전** 알림 제공

### 🧹 채널 청소

| 명령어 | 설명 |
|--------|------|
| `/청소` | 현재 시점 이전 채널 메시지 전부 삭제 |

> `메시지 관리` 권한이 있는 멤버만 사용할 수 있습니다.
<br/>

## 📁 프로젝트 구조

```
Smart-Mango/
├── bot.py              # 봇 진입점, Cog 로딩 및 명령어 동기화
├── config.py           # 환경 변수 및 기본 설정값
├── requirements.txt    # 의존성 패키지 목록
├── cogs/
│   ├── music.py        # 유튜브 음악 재생 & 대기열 관리
│   ├── voice.py        # TTS (gTTS 기반)
│   ├── pomodoro.py     # 뽀모도로 타이머
│   ├── clean.py        # 채널 메시지 청소
│   └── help.py         # 도움말
└── utils/
    └── state.py        # 서버별 상태 관리 (음악 큐, TTS, 뽀모도로)
```
<br/>

## 📦 주요 의존성

| 패키지 | 용도 |
|--------|------|
| `discord.py[voice]` | 디스코드 봇 프레임워크 |
| `yt-dlp` | 유튜브 오디오 추출 |
| `gTTS` | Google Text-to-Speech |
| `PyNaCl` | 음성 채널 암호화 |
| `python-dotenv` | 환경 변수 관리 |
<br/>

<div align="center">

Made with 🥭 and Python

</div>
