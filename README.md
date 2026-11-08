# NeverSearch

[ 🇷🇺 Русский ](#-русский) | [ 🇬🇧 English ](#-english)

---

<a id="-русский"></a>
## 🇷🇺 Русский

**NeverSearch** («Никогда не ищи») — консольный клиент для пакетного поиска и загрузки медиафайлов с Rule34 и Gelbooru с автоматической упаковкой в шифрованный контейнер 7-Zip (AES-256). Поддерживает Windows (PowerShell/CMD) и Android (Termux).

### Возможности

- **Поиск**: по одиночным и составным тегам (`oguri_cap solo ass 20`), художникам (`artist <имя>`) и франшизам.
- **Источники**: быстрое переключение между базами Rule34 и Gelbooru (`src [r34|gel]`).
- **Черный список (Blacklist)**: отсечение нежелательного контента по тегам (`bl on/off/add/del/list/clear`, по умолчанию блокирует futanari, guro, scat).
- **Режимы видео**: выгрузка только видеофайлов и анимаций (`video only`), совмещенный режим (`video on`) или только статичные арты (`video off`).
- **Фильтрация контента**: отсечение AI-генераций (`ai on/off`) и минимальный порог рейтинга (`score <N>`).
- **Автоматическое шифрование**: сохранение в единый зашифрованный контейнер 7z (`-mhe=on`, пароль по умолчанию: `v1zhik`).
- **Локальная дедупликация**: автоматический пропуск ранее скачанных постов по внутренней базе ID.
- **Автодополнение**: интерактивные подсказки тегов по клавише `TAB`.
- **Бесшовное OTA-обновление**: проверка и применение обновлений при запуске.

### Быстрая установка

#### Windows

Выполните в PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://gist.githubusercontent.com/vanadeyS/fd557488cadf0371fb235876bb85c9f2/raw/install_windows.ps1 | iex"
```

Команда `r34` регистрируется в системе и доступна из любой консоли.

#### Android (Termux)

Выполните в Termux:

```bash
pkg install -y curl && curl -fL https://gist.githubusercontent.com/vanadeyS/fd557488cadf0371fb235876bb85c9f2/raw/install_termux.sh -o ~/install_termux.sh && bash ~/install_termux.sh
```

Запуск: `r34`.

### Таблица команд

| Команда | Описание |
|---|---|
| `<тег(и)> [N\|all]` | Скачать посты по тегам (например: `oguri_cap solo ass 20`) |
| `artist <имя> [N\|all]` | Скачать работы указанного автора |
| `src [r34\|gel]` | Переключить источник (Rule34 / Gelbooru) |
| `bl [on\|off\|add\|del\|list]` | Управление черным списком тегов |
| `video [on\|off\|only]` | Режимы загрузки видеофайлов (`only` — строго видео) |
| `score <N>` | Порог минимального рейтинга |
| `count <N>` | Лимит скачивания по умолчанию |
| `ai on/off` | Фильтр AI-генераций |
| `list` | Список содержимого контейнера |
| `set` | Меню конфигурации (язык, пароль, API Hook, черный список) |
| `info` / `help` | Полная справка по хранилищу и синтаксису |
| `update` | Проверка и установка OTA-обновлений |
| `clean all` | Очистка рабочей папки |
| `mouse [on\|off]` | Включить/выключить поддержку мыши (Shift+Ctrl+Колесо для зума) |
| `theme [mono\|blue]` | Переключить цветовую палитру логотипа (Mono / Blue) |
| `clear` / `cls` | Очистить экран |
| `exit` / `q` | Выход из программы |

### Хранилище

- **Windows**: `%USERPROFILE%\Documents\NeverSearch\Bible.7z` (с обратной совместимостью с каталогом `umaZhickR34`)
- **Android**: `/storage/emulated/0/Documents/NeverSearch/Bible.7z` (или fallback в `$HOME/storage/shared/Documents` / `~/Documents/NeverSearch`)
- **Конфигурация**: `~/.r34_config.json` (в Windows защищен через DPAPI, в Termux правами `0600`).

---

<a id="-english"></a>
## 🇬🇧 English

**NeverSearch** ("Never Search") is a command-line client for batch searching and downloading media from Rule34 and Gelbooru, packaged automatically into an encrypted 7-Zip container (AES-256). Supports Windows (PowerShell/CMD) and Android (Termux).

### Features

- **Search**: single and multi-tag queries (`oguri_cap solo ass 20`), artists (`artist <name>`), and franchises.
- **Engines**: fast switching between Rule34 and Gelbooru databases (`src [r34|gel]`).
- **Tag Blacklist**: filter out unwanted content (`bl on/off/add/del/list/clear`, default blocks futanari, guro, scat).
- **Video Modes**: download animations/videos exclusively (`video only`), images and videos (`video on`), or static images only (`video off`).
- **Filters**: AI generator suppression (`ai on/off`) and minimum score threshold (`score <N>`).
- **Container Encryption**: all files are packed into a single AES-256 7z archive (`-mhe=on`, default password: `v1zhik`).
- **Deduplication**: previously saved posts are automatically skipped using internal ID caching.
- **Autocomplete**: real-time tag completions triggered via `TAB`.
- **Seamless OTA**: automatic version check and update on startup.

### Quick Install

#### Windows

Run in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://gist.githubusercontent.com/vanadeyS/fd557488cadf0371fb235876bb85c9f2/raw/install_windows.ps1 | iex"
```

The `r34` command is added to your PATH and ready to use immediately.

#### Android (Termux)

Run in Termux:

```bash
pkg install -y curl && curl -fL https://gist.githubusercontent.com/vanadeyS/fd557488cadf0371fb235876bb85c9f2/raw/install_termux.sh -o ~/install_termux.sh && bash ~/install_termux.sh
```

Launch with: `r34`.

### Command Reference

| Command | Description |
|---|---|
| `<tag(s)> [N\|all]` | Download posts by tags (e.g.: `oguri_cap solo ass 20`) |
| `artist <name> [N\|all]` | Download works by specified artist |
| `src [r34\|gel]` | Toggle search provider (Rule34 / Gelbooru) |
| `bl [on\|off\|add\|del\|list]` | Manage tag blacklist |
| `video [on\|off\|only]` | Video download mode (`only` — exclusively videos) |
| `score <N>` | Set minimum score threshold |
| `count <N>` | Set default batch limit |
| `ai on/off` | Toggle AI generator filter |
| `list` | Show contents of the encrypted container |
| `set` | Settings menu (language, vault password, API Hook, blacklist) |
| `info` / `help` | Manual for storage hierarchy, formats, and syntax |
| `update` | Check and apply OTA updates |
| `clean all` | Purge working directory |
| `mouse [on\|off]` | Toggle mouse support (Shift+Ctrl+Wheel for terminal zoom) |
| `theme [mono\|blue]` | Switch logo color palette (Mono / Blue) |
| `clear` / `cls` | Clear terminal screen |
| `exit` / `q` | Exit application |

### Storage & Security

- **Windows**: `%USERPROFILE%\Documents\NeverSearch\Bible.7z` (with backward compatibility for `umaZhickR34`)
- **Android**: `/storage/emulated/0/Documents/NeverSearch/Bible.7z` (or fallback to `$HOME/storage/shared/Documents` / `~/Documents/NeverSearch`)
- **Settings**: `~/.r34_config.json` (secured via Windows DPAPI on Windows, file mode `0600` on Termux).
