#!/usr/bin/env python3
# =====================================================================
# NeverSearch
# Author: vanadeyS (https://github.com/vanadeyS)
# Official Repository: https://github.com/vanadeyS/AlwaysSearch
# Copyright (c) 2026 vanadeyS. Licensed under the MIT License.
# =====================================================================
import base64
import copy
import ctypes
import getpass
import importlib
import importlib.util
import json
import py_compile
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, urlsplit


def install_python_dependencies():
    packages = {"requests": "requests", "prompt_toolkit": "prompt_toolkit"}
    missing = [package for module, package in packages.items() if not importlib.util.find_spec(module)]
    if not missing:
        return
    print("[*] Installing Python dependencies: " + ", ".join(missing))
    commands = []
    if os.name != "nt":
        commands.append([sys.executable, "-m", "pip", "install", "--break-system-packages", *missing])
        commands.append([sys.executable, "-m", "pip", "install", "--user", *missing])
    commands.append([sys.executable, "-m", "pip", "install", *missing])
    success = False
    for cmd in commands:
        result = subprocess.run(cmd)
        if result.returncode == 0:
            success = True
            break
    if not success:
        print("[-] Dependency installation failed. Run: pip install requests prompt_toolkit")
        raise SystemExit(1)
    importlib.invalidate_caches()


install_python_dependencies()

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter
from prompt_toolkit.styles import Style

VERSION = "1.05.03"
UPDATE_URL = "https://raw.githubusercontent.com/vanadeyS/AlwaysSearch/main/r34_gallery.py"
AUTHOR = "vanadeyS"
AUTHOR_GITHUB = "https://github.com/vanadeyS"

DEFAULT_PASSWORD = "v1zhik"


def get_root_dir():
    candidates = []
    if os.name == "nt":
        try:
            import ctypes.wintypes
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
            if buf.value:
                candidates.append(Path(buf.value))
        except Exception:
            pass
        for env_var in ("OneDrive", "OneDriveConsumer", "USERPROFILE"):
            val = os.environ.get(env_var)
            if val:
                d = Path(val) / "Documents"
                if d.is_dir():
                    candidates.append(d)
        candidates.append(Path.home() / "Documents")
    else:
        candidates.extend([
            Path("/storage/emulated/0/Documents"),
            Path.home() / "storage" / "shared" / "Documents",
            Path("/storage/emulated/0/Download"),
            Path.home() / "Documents",
        ])
    for base in candidates:
        if base.is_dir() or (base.parent.is_dir() and os.access(str(base.parent), os.W_OK)):
            old_p = base / "umaZhickR34"
            new_p = base / "NeverSearch"
            if old_p.is_dir() and not new_p.is_dir():
                return old_p
            return new_p
    return Path.home() / "Documents" / "NeverSearch"

ROOT_DIR = get_root_dir()
CONFIG_PATH = Path.home() / ".r34_config.json"
PROVIDERS = {
    "rule34": {
        "name": "Rule34",
        "api_url": "https://api.rule34.xxx/index.php",
        "autocomplete_url": "https://api.rule34.xxx/autocomplete.php",
    },
    "gelbooru": {
        "name": "Gelbooru",
        "api_url": "https://gelbooru.com/index.php",
        "autocomplete_url": "https://gelbooru.com/index.php?page=autocomplete2",
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
DEFAULTS = {
    "lang": "ru",
    "provider": "rule34",
    "min_score": 200,
    "scores": {"rule34": 200, "gelbooru": 0},
    "default_count": 20,
    "filter_ai": True,
    "include_video": False,
    "video_mode": "off",
    "blacklist": ["futanari", "guro", "scat"],
    "filter_bl": True,
    "theme": "blue",
    "api_key": "",
    "user_id": "",
    "gel_api_key": "",
    "gel_user_id": "",
    "vault_name": "Bible",
    "vault_pass": DEFAULT_PASSWORD,
    "folder_prefix": "R34",
}

TEXT = {
    "ru": {
        "vault_lbl": "Архив",
        "syntax_hdr": "Синтаксис:",
        "cmd_hdr": "Команды:",
        "banner_tag": "тег [теги...] [кол-во|all] (например: furina solo ass 20)",
        "banner_art": "artist <имя> [кол-во]  (например: artist rensuke 20)",
        "banner_fra": "франшиза <кол-во>     (например: genshin_impact 30)",
        "cmd_score": "мин. рейтинг (текущий: {val})",
        "cmd_count": "лимит по умолчанию (текущий: {val})",
        "cmd_ai": "фильтр нейросетей ({val})",
        "cmd_video": "скачивать ролики ({val})",
        "cmd_info": "справка по хранилищу и формату",
        "cmd_list": "список содержимого архива",
        "cmd_set": "настройки хранилища и ключей",
        "cmd_update": "проверить обновления",
        "cmd_clean": "удалить ВСЁ (включая архив)",
        "cmd_exit": "очистка / выход",
        "on": "вкл", "off": "выкл", "active": "АКТИВЕН", "offline": "НЕТ",
        "attached": "УКАЗАН", "none": "НЕТ",
        "no_posts": "Ничего не найдено по запросу.",
        "api_err": "Ошибка соединения с {provider} API.",
        "already_saved": "Все посты уже скачаны в архив.",
        "downloading": "Скачивание",
        "vault_updated": "Контейнер обновлен",
        "cfg_title": "=== Конфигурация ===",
        "cfg_lang": "Язык / Lang",
        "cfg_hook": "API Hook",
        "cfg_vault": "Настройки архива     : (имя, пароль, префикс)",
        "cfg_info": "Справка / Инфо       : (пути, распаковка, синтаксис)",
        "cfg_score": "Мин. Score",
        "cfg_count": "Лимит закачки",
        "cfg_ai": "Фильтр ИИ",
        "cfg_video": "Видеофайлы",
        "cfg_reset": "Сброс настроек",
        "cfg_back": "Назад",
        "vault_title": "=== Настройки контейнера ===",
        "vault_name": "Имя файла архива",
        "vault_pass": "Пароль архива",
        "vault_pfx": "Префикс подпапок",
        "info_title": "=== СПРАВКА И РАБОТА С ХРАНИЛИЩЕМ ===",
        "info_sec1": "1. Расположение и структура файлов:",
        "info_sec1_desc": "   Папка:   {root}\n   Файл:    {vault_name}\n   Путь:    {vault_path}\n   Внутри архива структура разделена по источникам:\n     Rule34:   [Франшиза]/[Префикс_Персонаж]/<id>_score_<рейтинг>.<ext>\n     Gelbooru: Gelbooru/[Франшиза]/[GEL_Персонаж]/<id>_score_<рейтинг>.<ext>\n     Авторы:   Artists/... или Gelbooru/Artists/...\n   Раздельное хранение исключает конфликт одинаковых ID постов.",
        "info_sec2": "2. Как искать и качать:",
        "info_sec2_desc": "   • Поиск персонажа: furina_(genshin_impact) 15\n     Скрипт сам создаст раздел 'Genshin_Impact' и положит файлы в 'R34_Furina'.\n   • Составной поиск по тегам: furina solo ass 20\n     Теги разделяются пробелом. Последнее число — лимит скачивания.\n   • Поиск по художнику: artist rensuke 20 (или 'all' для полной выкачки).\n   • Поиск по франшизе: zenless_zone_zero 30\n   • Автодополнение тегов: клавиша TAB при наборе тега.\n   • Источники (команда 'src [r34|gel]' или меню set):\n     Быстрое переключение между базами Rule34 и Gelbooru.\n   • Черный список (команда 'bl'):\n     'bl on' / 'bl off' — вкл/выкл фильтрацию (по умолчанию включена).\n     'bl add <тег>' / 'bl del <тег>' — добавить/удалить тег из фильтра.\n     'bl list' — просмотр списка (блокирует futanari, guro, scat и др.).\n   • Режимы видео (команда 'video' или меню set):\n     'video only' — качать строго видео и анимации (отсекает статичные арты).\n     'video on' — качать и арты, и видеофайлы.\n     'video off' — скачивать только статичные арты (без видео).\n   • Количество постов и лимиты API:\n     Счетчик 'доступно N постов' берется из базы выбранного источника.\n     Гостевой доступ без API-ключа может ограничивать число страниц.\n   • Повторные скачивания не дублируются: скрипт сверяет ID с уже сохраненными.",
        "info_sec3": "3. Извлечение и перенос на ПК / телефон:",
        "info_sec3_desc": "   • Архив зашифрован 7z (AES-256) с параметром -mhe=on.\n     Без пароля нельзя увидеть даже список файлов внутри.\n   • Пароль: защищен мастер-ключом в настройках (задается при первом старте или в меню set).\n   • Чем открывать на Android: ZArchiver, MiXplorer, Solid Explorer.\n   • Чем открывать на ПК: 7-Zip, WinRAR.\n   • Переносить можно обычным копированием файла {vault_name} через проводник.",
        "info_purpose": "4. Для чего нужна программа:",
        "info_purpose_desc": "   Программа ищет публикации на Rule34 по тегам и сохраняет их\n   в один зашифрованный архив. Файлы раскладываются по франшизам,\n   персонажам и художникам. Повторно скачанные ID пропускаются.\n   Софт не является облаком: архив и настройки находятся только\n   на этом устройстве. Для резервной копии скопируйте архив\n   на другой носитель, пока программа закрыта.",
        "info_api": "5. Подключение API (Rule34 и Gelbooru):",
        "info_api_desc": "   Ключи у каждого сервиса СВОИ (ключ от Rule34 не подходит к Gelbooru).\n   • Rule34 (не обязателен, но снимает лимиты):\n     1. Войдите на rule34.xxx -> My Account -> Manage API Keys.\n     2. Скопируйте api_key и числовой user_id.\n     3. Переключитесь на Rule34 ('src r34'), меню set -> пункт 3.\n     4. Вставьте: api_key=ВАШ_КЛЮЧ&user_id=ВАШ_ID\n   • Gelbooru (ОБЯЗАТЕЛЕН для загрузок):\n     1. Войдите на gelbooru.com -> Options -> API Access / Key.\n     2. Скопируйте User ID (цифры) и API Key (хэш-ключ).\n     3. Переключитесь на Gelbooru ('src gel'), меню set -> пункт 3.\n     4. Вставьте: api_key=ВАШ_КЛЮЧ&user_id=ВАШ_ID\n     Статус API Hook переключается независимо для каждого источника.",
        "info_security": "6. Защита данных и удаление:",
        "info_security_desc": "   • Windows шифрует сохраненные пароли и ключи через DPAPI.\n     В Termux настройки доступны только владельцу (права 600).\n   • Смена пароля архива сначала создает новый архив и только\n     после успеха заменяет старый. Ошибка не удаляет оригинал.\n   • Ошибка упаковки сохраняет загрузки в папке _failed_*.\n   • clean all и полное удаление требуют отдельного подтверждения.\n   • Полное удаление стирает программу, настройки, ключи и архив\n     без возможности восстановления. Сначала сделайте копию.",
        "press_enter": "Нажмите [Enter] для возврата в консоль...",
        "cfg_uninstall": "Полностью удалить софт и данные",
        "lang_prompt": "Язык (ru / en): ",
        "api_prompt": "Данные API (api_key=...&user_id=...) или 'off': ",
        "bad_format": "Неверный формат.",
        "reset_confirm": "Сбросить настройки? API-ключи будут удалены (y/N): ",
        "reset_done": "Настройки сброшены.",
        "score_prompt": "Минимальный рейтинг: ",
        "count_prompt": "Лимит загрузки: ",
        "name_prompt": "Имя архива без .7z: ",
        "prefix_prompt": "Префикс (максимум 5 символов): ",
        "current_password": "Текущий пароль: ",
        "new_password": "Новый пароль: ",
        "repeat_password": "Повторите пароль: ",
        "wrong_password": "Неверный текущий пароль.",
        "password_mismatch": "Пароли не совпадают.",
        "password_changed": "Пароль изменен.",
        "password_unpack_error": "Не удалось распаковать архив.",
        "password_rekey_error": "Не удалось создать новый архив. Старый архив сохранен.",
        "seven_zip_missing": "7z не найден. Установите 7-Zip (Termux: pkg install 7zip).",
        "update_missing_version": "В обновлении не указана версия",
        "update_current": "Установлена последняя версия (v{version}).",
        "update_error": "Ошибка проверки обновления: {error}",
        "archive_empty": "Архив {name} пуст или отсутствует.",
        "archive_read_error": "Ошибка чтения архива. Проверьте пароль.",
        "staging_busy": "Другая загрузка уже использует каталог _staging.",
        "archive_open_error": "Не удалось открыть архив. Проверьте пароль.",
        "download_failed": "Ни один файл не был скачан. Архив не изменен.",
        "archive_error": "Ошибка 7z. Скачанные файлы сохранены в {name}",
        "download_success": "Успешно: {done} / {total}",
        "interactive_only": "Запустите программу в интерактивном терминале.",
        "storage_denied": "Нет доступа к {path}: {error}",
        "storage_hint": "В Termux выполните: termux-setup-storage",
        "clean_confirm": "Удалить всё содержимое {path}? Введите DELETE: ",
        "clean_done": "Каталог очищен.",
        "cancelled": "Отменено.",
        "uninstall_title": "=== ПОЛНОЕ УДАЛЕНИЕ ===",
        "uninstall_warning": "Будут удалены программа, настройки, ключи, архивы и все загрузки.\nВосстановить данные после удаления нельзя.",
        "uninstall_paths": "Данные: {root}\nНастройки: {config}\nПрограмма: {program}",
        "uninstall_confirm": "Введите DELETE для подтверждения: ",
        "uninstall_done": "Удаление завершено.",
        "uninstall_error": "Не удалось удалить: {path}. Закройте файлы и удалите вручную.",
        "shutdown": "Завершение работы.",
        "protect_error": "Не удалось защитить учетные данные Windows",
        "install_7zip": "Установка системных пакетов: 7zip",
        "install_7zip_hint": "Для архива установите 7-Zip.",
        "cmd_src": "источник поиска ({src})",
        "cmd_video_mode": "режим видео ({mode})",
        "cmd_bl": "черный список ({state}, {count})",
        "cmd_theme": "тема оформления ({val})",
        "cfg_theme": "Тема оформления (Theme)",
        "theme_switched": "Тема оформления переключена на: {name}",
        "cfg_src": "Источник (Source)",
        "cfg_bl": "Черный список (BL)",
        "cfg_video_mode": "Режим видео",
        "tags_count": "{count} тегов",
        "src_switched": "Источник переключен на: {name}",
        "api_rejected": "API-ключ или User ID не приняты {provider}.",
        "bl_title": "=== ЧЕРНЫЙ СПИСОК ТЕГОВ ===",
        "bl_status_lbl": "Статус",
        "bl_current_tags": "Текущие теги ({count}): {tags}",
        "bl_empty": "(пусто)",
        "bl_opt_toggle": "Включить / Выключить фильтр",
        "bl_opt_add": "Добавить тег",
        "bl_opt_del": "Удалить тег",
        "bl_opt_clear": "Очистить весь список",
        "bl_prompt_add": "Тег для блокировки (например: futanari): ",
        "bl_prompt_del": "Тег для удаления: ",
        "bl_added": "Добавлено: {tag}",
        "bl_deleted": "Удалено: {tag}",
        "bl_cleared": "Список очищен.",
        "clean_confirm_all": "Удалить всё содержимое {root}? Введите DELETE: ",
        "clean_purged": "Папка очищена.",
        "pass_prompt_init": "Задайте пароль архива (минимум 4 символа): ",
        "pass_repeat_init": "Повторите пароль архива: ",
        "pass_short": "Пароль слишком короткий (минимум 4 символа).",
        "pass_default_confirm": "Оставить пароль по умолчанию? (y/N): ",
        "no_posts_score": "Постов с рейтингом >= {score} не найдено (доступно {count} без фильтра). Попробуйте 'score 0'.",
        "searching_api": "Поиск в {provider}...",
        "checking_vault": "Проверка хранилища {archive}...",
        "scanning_pages": "Поиск постов [стр. {page} | отобрано {count}/{limit}]...", 
        "auth_required": "Требуется привязать {provider} API (api_key и user_id) в меню 'set' (пункт 3).",
        "gelbooru_auth_hint": "Для Gelbooru API требуются api_key и user_id в меню 'set' (пункт 3).",
        "installed_path": "Путь",
        "stats_summary": "Всего: {total} | В хранилище: {known} | Доступно: {available}",
        "bl_updated": "Черный список: {tags}",
        "pass_warn": "рекомендуется сменить",
        "pass_first_hint": "Установлен пароль по умолчанию. Рекомендуется сменить его в меню 'set' -> 4.",
        "theme_set": "Тема оформления: {theme}",
        "video_mode_set": "Режим видео: {mode}",
        "source_set": "Источник: {source} | score: {score}",
        "bl_set": "Черный список: {status}",
        "bl_list_hdr": "Черный список [{state}]: {tags}",
        "net_page_warning": "Связь с сервером прервана при поиске страниц. Загрузка продолжена с найденными постами.",
    },
    "en": {
        "vault_lbl": "Vault", "syntax_hdr": "Syntax:", "cmd_hdr": "Commands:",
        "banner_tag": "tag [tags...] [count|all] (e.g.: furina solo ass 20)",
        "banner_art": "artist <name> [count]    (e.g.: artist rensuke 20)",
        "banner_fra": "franchise <count>      (e.g.: genshin_impact 30)",
        "cmd_score": "min score threshold (current: {val})",
        "cmd_count": "default batch count (current: {val})",
        "cmd_ai": "AI generator filter ({val})",
        "cmd_video": "download videos ({val})",
        "cmd_info": "storage & usage manual", "cmd_list": "list vault contents",
        "cmd_set": "configuration & vault settings", "cmd_update": "check for updates",
        "cmd_clean": "purge ALL (including archive)", "cmd_exit": "clear / exit",
        "on": "on", "off": "off", "active": "ACTIVE", "offline": "OFFLINE",
        "attached": "ATTACHED", "none": "NONE",
        "no_posts": "No posts found.", "api_err": "Error connecting to {provider} API.",
        "already_saved": "All posts are already cached in vault.",
        "downloading": "Downloading", "vault_updated": "Vault updated",
        "cfg_title": "=== Configuration ===", "cfg_lang": "Language", "cfg_hook": "API Hook",
        "cfg_vault": "Vault Storage Setup  : (name, password, prefix)",
        "cfg_info": "User Guide / Info    : (paths, extraction, syntax)",
        "cfg_score": "Min Score", "cfg_count": "Batch Limit", "cfg_ai": "AI Filter",
        "cfg_video": "Video Files", "cfg_token": "GitHub Token",
        "cfg_reset": "Reset to Defaults", "cfg_back": "Back",
        "vault_title": "=== Vault Configuration ===", "vault_name": "Archive filename",
        "vault_pass": "Archive password", "vault_pfx": "Subfolder prefix",
        "info_title": "=== USER GUIDE & STORAGE MANUAL ===",
        "info_sec1": "1. File Location & Storage Hierarchy:",
        "info_sec1_desc": "   Folder:   {root}\n   Archive:  {vault_name}\n   Path:     {vault_path}\n   Internal container structure separated by provider:\n     Rule34:   [Franchise]/[Prefix_Character]/<id>_score_<score>.<ext>\n     Gelbooru: Gelbooru/[Franchise]/[GEL_Character]/<id>_score_<score>.<ext>\n     Artists:  Artists/... or Gelbooru/Artists/...\n   Independent paths prevent duplicate ID clashes across services.",
        "info_sec2": "2. Search Syntax & Downloading:",
        "info_sec2_desc": "   • Character query: furina_(genshin_impact) 15\n     Automatically sorts by franchise: 'Genshin_Impact' folder and 'R34_Furina' subfolder.\n   • Multi-tag search: furina solo ass 20\n     Space-separated tags. The trailing number sets the download count.\n   • Artist query: artist rensuke 20 (or 'all' for complete archive).\n   • Franchise query: zenless_zone_zero 30\n   • Autocomplete: press TAB while typing tags.\n   • Provider switch ('src [r34|gel]' or set menu):\n     Toggle search between Rule34 and Gelbooru engines.\n   • Blacklist filter ('bl'):\n     'bl on' / 'bl off' — toggle tag filtering (enabled by default).\n     'bl add <tag>' / 'bl del <tag>' — add/remove excluded tags.\n     'bl list' — view blocked tags (defaults: futanari, guro, scat).\n   • Video modes ('video' or set menu):\n     'video only' — download exclusively animations & video files.\n     'video on' — download both images and videos.\n     'video off' — download static images only.\n   • API limits and post counts:\n     Displayed count is returned by booru API index for matching posts.\n     Guest queries without API key may have capped pagination limits.\n   • Deduplication: already downloaded post IDs are skipped.",
        "info_sec3": "3. Extraction & Transfer (PC / Android):",
        "info_sec3_desc": "   • Container is secured with AES-256 and encrypted headers (-mhe=on).\n     Filenames are completely hidden until decrypted.\n   • Password: secured via master key in settings (configured on first launch or in set menu).\n   • Recommended Android unpackers: ZArchiver, MiXplorer, Solid Explorer.\n   • Recommended PC unpackers: 7-Zip, WinRAR.\n   • Simply copy {vault_name} to PC or flash drive via standard file manager.",
        "info_purpose": "4. What this program does:",
        "info_purpose_desc": "   The program finds Rule34 posts by tags and saves them in one\n   encrypted archive. Files are sorted by franchise, character and\n   artist. IDs that were downloaded before are skipped.\n   This is not a cloud service: the archive and settings stay on\n   this device. For a backup, copy the archive to another drive\n   while the program is closed.",
        "info_api": "5. API Configuration (Rule34 & Gelbooru):",
        "info_api_desc": "   Each provider requires its own dedicated credentials.\n   • Rule34 (optional, lifts rate limits):\n     1. Sign in to rule34.xxx -> My Account -> Manage API Keys.\n     2. Copy api_key and numeric user_id.\n     3. Switch to Rule34 ('src r34'), go to set menu -> item 3.\n     4. Paste: api_key=YOUR_KEY&user_id=YOUR_ID\n   • Gelbooru (REQUIRED for scraping & pagination):\n     1. Sign in to gelbooru.com -> Options -> API Access / Key.\n     2. Copy User ID and API Key (hash string).\n     3. Switch to Gelbooru ('src gel'), go to set menu -> item 3.\n     4. Paste: api_key=YOUR_KEY&user_id=YOUR_ID\n     API Hook status reflects the currently active provider.",
        "info_security": "6. Data protection and deletion:",
        "info_security_desc": "   • Windows encrypts saved passwords and keys with DPAPI.\n     In Termux, only the device user can read settings (mode 600).\n   • Changing the archive password creates a replacement first\n     and replaces the original only after a successful operation.\n   • If packing fails, downloads are kept in a _failed_* folder.\n   • clean all and full removal require separate confirmation.\n   • Full removal erases the program, settings, keys and archive\n     permanently. Make a backup before using it.",
        "press_enter": "Press [Enter] to return...",
        "cfg_uninstall": "Completely remove software and data",
        "lang_prompt": "Language (ru / en): ",
        "api_prompt": "API credentials (api_key=...&user_id=...) or 'off': ",
        "bad_format": "Invalid format.",
        "reset_confirm": "Reset settings? API keys will be removed (y/N): ",
        "reset_done": "Settings reset.",
        "score_prompt": "Minimum score: ",
        "count_prompt": "Download limit: ",
        "name_prompt": "Archive name without .7z: ",
        "prefix_prompt": "Prefix (maximum 5 characters): ",
        "current_password": "Current password: ",
        "new_password": "New password: ",
        "repeat_password": "Repeat password: ",
        "wrong_password": "Incorrect current password.",
        "password_mismatch": "Passwords do not match.",
        "password_changed": "Password changed.",
        "password_unpack_error": "Could not extract the archive.",
        "password_rekey_error": "Could not create the new archive. The original is intact.",
        "seven_zip_missing": "7z not found. Install 7-Zip (Termux: pkg install 7zip).",
        "update_missing_version": "The update does not specify a version",
        "update_current": "You have the latest version (v{version}).",
        "update_error": "Update check failed: {error}",
        "cmd_src": "search provider ({src})",
        "cmd_video_mode": "video mode ({mode})",
        "cmd_bl": "blacklist filter ({state}, {count})",
        "cmd_theme": "color theme ({val})",
        "cfg_theme": "Color Theme",
        "theme_switched": "Color theme switched to: {name}",
        "cfg_src": "Search Provider",
        "cfg_bl": "Blacklist Filter",
        "cfg_video_mode": "Video Mode",
        "tags_count": "{count} tags",
        "src_switched": "Provider switched to: {name}",
        "api_rejected": "API key or User ID rejected by {provider}.",
        "bl_title": "=== TAG BLACKLIST ===",
        "bl_status_lbl": "Status",
        "bl_current_tags": "Current tags ({count}): {tags}",
        "bl_empty": "(empty)",
        "bl_opt_toggle": "Toggle Filter ON / OFF",
        "bl_opt_add": "Add tag",
        "bl_opt_del": "Remove tag",
        "bl_opt_clear": "Clear all tags",
        "bl_prompt_add": "Tag to block (e.g.: futanari): ",
        "bl_prompt_del": "Tag to remove: ",
        "bl_added": "Added: {tag}",
        "bl_deleted": "Removed: {tag}",
        "bl_cleared": "Blacklist cleared.",
        "clean_confirm_all": "Purge entire folder {root}? Type DELETE: ",
        "clean_purged": "Folder purged.",
        "pass_prompt_init": "Set vault password (min 4 chars): ",
        "pass_repeat_init": "Repeat vault password: ",
        "pass_short": "Password too short (min 4 chars).",
        "pass_default_confirm": "Keep default password? (y/N): ",
        "no_posts_score": "No posts matching score >= {score} ({count} available without filter). Try 'score 0'.",
        "searching_api": "Searching {provider}...",
        "checking_vault": "Checking {archive} vault...",
        "scanning_pages": "Scanning posts [page {page} | found {count}/{limit}]...", 
        "auth_required": "Authentication required: configure {provider} API (api_key & user_id) in 'set' menu (item 3).",
        "gelbooru_auth_hint": "Gelbooru API requires api_key and user_id in 'set' menu (item 3).",
        "installed_path": "Path",
        "stats_summary": "Total: {total} | In vault: {known} | Available: {available}",
        "bl_updated": "Blacklist: {tags}",
        "pass_warn": "recommended to change",
        "pass_first_hint": "Default password set. Recommended to change via 'set' -> 4.",
        "theme_set": "Color theme: {theme}",
        "video_mode_set": "Video mode: {mode}",
        "source_set": "Source: {source} | score: {score}",
        "bl_set": "Blacklist: {status}",
        "bl_list_hdr": "Blacklist [{state}]: {tags}",
        "net_page_warning": "Server connection interrupted while scanning pages. Proceeding with collected posts.",
        "archive_empty": "Archive {name} is empty or missing.",
        "archive_read_error": "Could not read the archive. Check the password.",
        "staging_busy": "Another download is already using the _staging directory.",
        "archive_open_error": "Could not open the archive. Check the password.",
        "download_failed": "No files were downloaded. The archive was not changed.",
        "archive_error": "7z error. Downloaded files were saved in {name}",
        "download_success": "Completed: {done} / {total}",
        "interactive_only": "Run the program in an interactive terminal.",
        "storage_denied": "Cannot access {path}: {error}",
        "storage_hint": "In Termux, run: termux-setup-storage",
        "clean_confirm": "Delete everything in {path}? Type DELETE: ",
        "clean_done": "Directory cleared.",
        "cancelled": "Cancelled.",
        "uninstall_title": "=== COMPLETE REMOVAL ===",
        "uninstall_warning": "The program, settings, keys, archives and all downloads will be deleted.\nThis data cannot be recovered.",
        "uninstall_paths": "Data: {root}\nSettings: {config}\nProgram: {program}",
        "uninstall_confirm": "Type DELETE to confirm: ",
        "uninstall_done": "Removal complete.",
        "uninstall_error": "Could not remove: {path}. Close open files and remove it manually.",
        "shutdown": "Shutting down.",
        "protect_error": "Could not protect Windows credentials",
        "install_7zip": "Installing system packages: 7zip",
        "install_7zip_hint": "Install 7-Zip to use the archive.",
    },
}


def unprotect_secret(value):
    if not isinstance(value, str) or not value.startswith("dpapi:"):
        return value
    if os.name != "nt":
        return ""
    class DataBlob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_byte))]
    try:
        raw = base64.b64decode(value[6:], validate=True)
        buffer = ctypes.create_string_buffer(raw)
        source = DataBlob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
        result = DataBlob()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)
        ):
            return ""
        try:
            return ctypes.string_at(result.data, result.size).decode("utf-8")
        finally:
            ctypes.windll.kernel32.LocalFree(result.data)
    except (ValueError, OSError, UnicodeError):
        return ""


def load_config():
    data = copy.deepcopy(DEFAULTS)
    try:
        stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(stored, dict):
            for key in DEFAULTS:
                if key in stored:
                    data[key] = stored[key]
    except (OSError, ValueError):
        pass
    data["provider"] = str(data.get("provider", "rule34")).lower()
    if data["provider"] not in PROVIDERS:
        data["provider"] = "rule34"
    if "scores" not in data or not isinstance(data.get("scores"), dict):
        data["scores"] = {"rule34": 200, "gelbooru": 0}
    prov = data.get("provider", "rule34")
    if prov == "gelbooru" and data["scores"].get("gelbooru", 0) > 50:
        data["scores"]["gelbooru"] = 0
    data["min_score"] = data["scores"].get(prov, 0 if prov == "gelbooru" else 200)
    data["scores"][prov] = data["min_score"]
    try:
        data["default_count"] = max(1, int(data["default_count"]))
    except (TypeError, ValueError):
        data["default_count"] = DEFAULTS["default_count"]
    for key in ("api_key", "user_id", "gel_api_key", "gel_user_id", "vault_pass"):
        data[key] = unprotect_secret(data[key])
    data["filter_ai"] = bool(data["filter_ai"])
    data["lang"] = data["lang"] if data["lang"] in TEXT else "ru"
    if "blacklist" not in data or not isinstance(data["blacklist"], list):
        data["blacklist"] = DEFAULTS["blacklist"][:]
    data["filter_bl"] = bool(data.get("filter_bl", True))
    data["theme"] = str(data.get("theme", "blue")).lower()
    if data["theme"] not in ("blue", "mono"):
        data["theme"] = "blue"
    data["video_mode"] = str(data.get("video_mode", "on" if data.get("include_video") else "off")).lower()
    if data["video_mode"] not in ("off", "on", "only"):
        data["video_mode"] = "off"
    data["include_video"] = data["video_mode"] in ("on", "only")
    return data


cfg = load_config()
secrets = {
    key: cfg.pop(key, "")
    for key in ("api_key", "user_id", "gel_api_key", "gel_user_id", "vault_pass")
}
local = threading.local()
class InterProcessLock:
    def __init__(self, lock_file):
        self.lock_file = Path(lock_file)
        self.fp = None

    def __enter__(self):
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.fp = open(self.lock_file, "a+")
        if os.name == "nt":
            import msvcrt
            start = time.time()
            while True:
                try:
                    self.fp.seek(0)
                    msvcrt.locking(self.fp.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() - start > 30:
                        raise TimeoutError("Vault is locked by another process.")
                    time.sleep(0.2)
        else:
            import fcntl
            start = time.time()
            while True:
                try:
                    fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (BlockingIOError, OSError):
                    if time.time() - start > 30:
                        raise TimeoutError("Vault is locked by another process.")
                    time.sleep(0.2)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.fp.seek(0)
                    msvcrt.locking(self.fp.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                self.fp.close()
            except Exception:
                pass
            self.fp = None


def is_pid_running(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except PermissionError:
            return True
        except OSError:
            return False


def get_staging_dir():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "NeverSearch" / "_staging"
    return Path.home() / ".NeverSearch_staging"


def clean_stale_staging():
    staging = get_staging_dir()
    if not staging.exists():
        return True
    pid_file = staging / ".pid"
    is_stale = False
    if pid_file.exists():
        try:
            raw = pid_file.read_text(encoding="utf-8").strip()
            parts = raw.split(":")
            pid = int(parts[0])
            if not is_pid_running(pid):
                is_stale = True
        except Exception:
            is_stale = True
    else:
        try:
            if time.time() - staging.stat().st_mtime > 1800:
                is_stale = True
        except Exception:
            pass
    if is_stale:
        shutil.rmtree(staging, ignore_errors=True)
        return True
    return False


archive_lock = threading.Lock()


def t(key, **values):
    lang = cfg["lang"] if cfg["lang"] in TEXT else "ru"
    value = TEXT[lang].get(key, TEXT["ru"].get(key, key))
    return value.format(**values) if values else value


def secret(key):
    return str(secrets.get(key, ""))


def protect_secret(value):
    if os.name != "nt":
        return value
    class DataBlob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_byte))]
    raw = value.encode("utf-8")
    buffer = ctypes.create_string_buffer(raw)
    source = DataBlob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    result = DataBlob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)
    ):
        raise OSError(t("protect_error"))
    try:
        encrypted = ctypes.string_at(result.data, result.size)
    finally:
        ctypes.windll.kernel32.LocalFree(result.data)
    return "dpapi:" + base64.b64encode(encrypted).decode("ascii")


def save_cfg():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    try:
        if CONFIG_PATH.is_file():
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                existing = raw
    except Exception:
        pass
    stored = dict(cfg)
    stored.update({key: protect_secret(secret(key)) for key in secrets})
    existing.update(stored)
    temporary = CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, CONFIG_PATH)
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass


def session():
    if not hasattr(local, "session"):
        s = requests.Session()
        s.headers.update(HEADERS)
        try:
            from urllib3.util import Retry
            from requests.adapters import HTTPAdapter
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], raise_on_status=False)
            adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
            s.mount("http://", adapter)
            s.mount("https://", adapter)
        except Exception:
            pass
        local.session = s
    return local.session


def get(url, **kwargs):
    response = session().get(url, **kwargs)
    response.raise_for_status()
    return response


def vault_path():
    name = safe_component(str(cfg.get("vault_name", "Bible")))
    if name.lower().endswith(".7z"):
        name = name[:-3]
    name = safe_component(name)
    return ROOT_DIR / f"{name or 'Bible'}.7z"


def vault_password():
    return secret("vault_pass") or DEFAULT_PASSWORD


def seven_zip():
    executable = shutil.which("7z") or shutil.which("7za") or shutil.which("7zz")
    if executable:
        return executable
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "7-Zip" / "7z.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "7-Zip" / "7z.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "7-Zip" / "7z.exe",
            Path(r"C:\Program Files\7-Zip\7z.exe"),
            Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
        ]
        for c in candidates:
            if c.is_file():
                return str(c)
    else:
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        for b in ("7zz", "7z", "7za"):
            cand = Path(prefix) / "bin" / b
            if cand.is_file() and os.access(cand, os.X_OK):
                return str(cand)
    return None


def run_7z(args, cwd=None):
    exe = seven_zip()
    if not exe:
        raise RuntimeError(t("seven_zip_missing"))
    return subprocess.run(
        [exe, *args], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[3J\033[2J\033[H", end="", flush=True)


def ensure_system_dependencies():
    if seven_zip():
        return
    if shutil.which("pkg"):
        print(f"[*] {t('install_7zip')}")
        subprocess.run(["pkg", "install", "-y", "7zip"])
    elif os.name == "nt" and shutil.which("winget"):
        subprocess.run(
            ["winget", "install", "--id", "7zip.7zip", "--exact", "--silent",
             "--accept-package-agreements", "--accept-source-agreements"]
        )
    else:
        print(f"[!] {t('install_7zip_hint')}")


THEMES = {
    "mono": [
        "\033[38;2;255;255;255m",
        "\033[38;2;225;225;225m",
        "\033[38;2;190;190;190m",
        "\033[38;2;155;155;155m",
        "\033[38;2;120;120;120m",
        "\033[38;2;85;85;85m",
    ],
    "blue": [
        "\033[38;2;135;235;255m",
        "\033[38;2;100;210;255m",
        "\033[38;2;65;180;255m",
        "\033[38;2;40;150;245m",
        "\033[38;2;20;120;225m",
        "\033[38;2;10;90;190m",
    ],
}

LOGO_WIDE = [
    "  ███╗  ██╗███████╗██╗   ██╗███████╗██████╗   ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗",
    "  ████╗ ██║██╔════╝██║   ██║██╔════╝██╔══██╗  ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║",
    "  ██╔██╗██║█████╗  ██║   ██║█████╗  ██████╔╝  ███████╗█████╗  ███████║██████╔╝██║     ███████║",
    "  ██║╚████║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗  ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║",
    "  ██║ ╚███║███████╗ ╚████╔╝ ███████╗██║  ██║  ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║",
    "  ╚═╝  ╚══╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝",
]

LOGO_STACKED = [
    "  ███╗  ██╗███████╗██╗   ██╗███████╗██████╗ ",
    "  ████╗ ██║██╔════╝██║   ██║██╔════╝██╔══██╗",
    "  ██╔██╗██║█████╗  ██║   ██║█████╗  ██████╔╝",
    "  ██║╚████║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗",
    "  ██║ ╚███║███████╗ ╚████╔╝ ███████╗██║  ██║",
    "  ╚═╝  ╚══╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝",
    "  ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗",
    "  ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║",
    "  ███████╗█████╗  ███████║██████╔╝██║     ███████║",
    "  ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║",
    "  ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║",
    "  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝",
]


def render_banner():
    theme_key = cfg.get("theme", "blue")
    palette = THEMES.get(theme_key, THEMES["blue"])
    div_color = "\033[38;2;60;60;60m" if theme_key == "mono" else "\033[38;2;20;75;160m"
    cols = shutil.get_terminal_size((100, 24)).columns
    logo_lines = LOGO_WIDE if cols >= 96 else LOGO_STACKED
    rendered = []
    pal_len = len(palette)
    for idx, line in enumerate(logo_lines):
        color = palette[idx % pal_len]
        rendered.append(f"{color}{line}\033[0m")
    rendered.append(f"{div_color}  " + "─" * min(cols - 4, 88) + "\033[0m")
    return "\n".join(rendered)


STYLE = Style.from_dict({
    "completion-menu.completion": "bg:#1c1c1c #cfcfcf",
    "completion-menu.completion.current": "bg:#3a3a3a #ffffff bold",
    "prompt": "#00d787 bold",
})


def print_banner():
    clear_screen()
    print(render_banner())
    ai = t("on") if cfg["filter_ai"] else t("off")
    v_mode = cfg.get("video_mode", "on" if cfg.get("include_video") else "off").upper()
    src_name = current_provider()["name"]
    bl_state = t("on").upper() if cfg.get("filter_bl", True) else t("off").upper()
    bl_cnt = len(cfg.get("blacklist", []))
    thm_name = cfg.get("theme", "blue").upper()
    print(f"  \033[90mvanadeyS \033[0m| NeverSearch v{VERSION} | [{cfg['lang'].upper()}] | {src_name} | {t('vault_lbl')}: \033[36m{vault_path().name}\033[0m")
    print(f"  \033[90m{AUTHOR_GITHUB} | {t('cfg_theme')}: {thm_name}\033[0m\n")
    print(f"  \033[1m{t('syntax_hdr')}\033[0m")
    print(f"    {t('banner_tag')}\n    {t('banner_art')}\n    {t('banner_fra')}\n")
    print(f"  \033[1m{t('cmd_hdr')}\033[0m")
    print(f"    score <N>       — {t('cmd_score', val=cfg['min_score'])}")
    print(f"    count <N>       — {t('cmd_count', val=cfg['default_count'])}")
    print(f"    src [r34|gel]   — {t('cmd_src', src=src_name)}")
    print(f"    ai on/off       — {t('cmd_ai', val=ai)}")
    print(f"    video on/off/only — {t('cmd_video_mode', mode=v_mode)}")
    print(f"    bl [on/off/add/del/list] — {t('cmd_bl', state=bl_state, count=bl_cnt)}")
    print(f"    theme [mono|blue] — {t('cmd_theme', val=thm_name)}")
    print(f"    info / help     — {t('cmd_info')}")
    print(f"    list            — {t('cmd_list')}")
    print(f"    set             — {t('cmd_set')}")
    print(f"    update          — {t('cmd_update')}")
    print(f"    clean all       — {t('cmd_clean')}")
    print(f"    clear / exit    — {t('cmd_exit')}\n")


def show_info():
    clear_screen()
    path = vault_path()
    print(f"\n\033[1m{t('info_title')}\033[0m\n")
    print(f"\033[36m{t('info_sec1')}\033[0m")
    print(t("info_sec1_desc", root=ROOT_DIR, vault_name=path.name, vault_path=path))
    print(f"\n\033[36m{t('info_sec2')}\033[0m\n{t('info_sec2_desc')}")
    print(f"\n\033[36m{t('info_sec3')}\033[0m")
    print(t("info_sec3_desc", vault_name=path.name))
    print(f"\n\033[36m{t('info_purpose')}\033[0m\n{t('info_purpose_desc')}")
    print(f"\n\033[36m{t('info_api')}\033[0m\n{t('info_api_desc')}")
    print(f"\n\033[36m{t('info_security')}\033[0m\n{t('info_security_desc')}")
    print(f"\n\033[36mАвтор / Author:\033[0m {AUTHOR} ({AUTHOR_GITHUB})")
    input(f"\n\033[90m{t('press_enter')}\033[0m")


def parse_version(value):
    parts = re.findall(r"\d+", value)
    return tuple(map(int, parts)) if parts else (0,)


def replace_program(source):
    destination = Path(__file__).resolve()
    compile(source, str(destination), "exec")
    temporary = destination.with_name(destination.name + ".new")
    backup = destination.with_name(destination.name + ".bak")
    try:
        temporary.write_text(source, encoding="utf-8")
        py_compile.compile(str(temporary), cfile=str(temporary) + "c", doraise=True)
        shutil.copy2(destination, backup)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
        Path(str(temporary) + "c").unlink(missing_ok=True)


def check_auto_update(silent=True):
    try:
        url = f"{UPDATE_URL}?t={int(time.time())}"
        response = get(url, headers={"Cache-Control": "no-cache"}, timeout=10)
        match = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', response.text, re.MULTILINE)
        if not match:
            raise ValueError(t("update_missing_version"))
        remote_version = match.group(1)
        if not ("NeverSearch" in response.text and "vanadeyS" in response.text):
            raise ValueError("Payload signature mismatch.")
        if parse_version(remote_version) > parse_version(VERSION):
            prompt_msg = f"\n\033[33m[!] Доступно обновление: v{remote_version} (текущая: v{VERSION}). Обновить? (Y/n): \033[0m" if cfg.get("lang") == "ru" else f"\n\033[33m[!] Update available: v{remote_version} (current: v{VERSION}). Update now? (Y/n): \033[0m"
            sys.stdout.write(prompt_msg)
            sys.stdout.flush()
            ans = sys.stdin.readline().strip().lower()
            if ans in ("", "y", "yes", "д", "да"):
                print(f"\033[32m[+] OTA Update: v{remote_version}\033[0m")
                replace_program(response.text)
                target_file = str(Path(__file__).resolve())
                if os.name == "nt":
                    subprocess.Popen([sys.executable, target_file])
                    sys.exit(0)
                else:
                    os.execv(sys.executable, [sys.executable, target_file])
        if not silent:
            print(f"[*] {t('update_current', version=VERSION)}")
    except (requests.RequestException, OSError, SyntaxError, ValueError) as error:
        if not silent:
            print(f"[-] {t('update_error', error=error)}")
    if not silent:
        time.sleep(1)



def safe_component(value):
    value = re.sub(r'[\/:*?"<>|\x00-\x1f]', "_", str(value or "").strip())
    value = re.sub(r'\.{2,}', "_", value)
    value = value.strip(". ")
    value = value.lstrip("-@")
    value = value.strip("._ ")
    return (value or "untitled")[:120]


def resolve_paths(tag, artist=False):
    prov = str(cfg.get("provider", "rule34")).lower()
    prefix = safe_component(cfg.get("folder_prefix", "")) if cfg.get("folder_prefix", "").strip() else ""
    if prov == "gelbooru":
        pfx = "GEL_" if prefix == "R34" or not prefix else f"{prefix}_"
        root_sec = "Gelbooru"
    else:
        pfx = f"{prefix}_" if prefix else "R34_"
        root_sec = ""

    if artist:
        art_name = safe_component(tag)
        franchise = f"{root_sec}/Artists" if root_sec else "Artists"
        return franchise, pfx + art_name

    tokens = tag.split()
    char_tokens = [t for t in tokens if '(' in t and ')' in t]
    primary = safe_component(char_tokens[0] if char_tokens else (tokens[0] if tokens else "untitled"))

    match = re.fullmatch(r"(.*?)_\((.*?)\)", primary)
    if match:
        fra = safe_component(match.group(2)).title()
        franchise = f"{root_sec}/{fra}" if root_sec else fra
        char_name = safe_component(match.group(1)).title()
        return franchise, pfx + char_name
    fra = primary.title()
    franchise = f"{root_sec}/{fra}" if root_sec else fra
    return franchise, pfx + primary.lower()


def auth_query():
    prov = str(cfg.get("provider", "rule34")).lower()
    if prov == "gelbooru":
        key, user = secret("gel_api_key").strip(), secret("gel_user_id").strip()
    else:
        key, user = secret("api_key").strip(), secret("user_id").strip()
    return f"&api_key={quote(key)}&user_id={quote(user)}" if key and user else ""


def filters(active_query=""):
    result = []
    if cfg["min_score"]:
        result.append(f"score:>={cfg['min_score']}")
    if cfg["filter_ai"]:
        result.append("-ai_generated -stable_diffusion -midjourney -novelai -nijijourney -dalle -ai_art -image_generation")
    v_mode = cfg.get("video_mode", "off")
    if v_mode == "only":
        result.append("video")
    elif v_mode == "off":
        result.append("-video -animated -mp4 -webm")
    active_tokens = set(re.findall(r"[a-zA-Z0-9_]+", active_query.lower()))
    if cfg.get("filter_bl", True) and cfg.get("blacklist"):
        for btag in cfg["blacklist"]:
            cleaned = btag.strip().replace(" ", "_")
            if cleaned and not cleaned.startswith("-"):
                if cleaned.lower() not in active_tokens:
                    result.append(f"-{cleaned}")
    return " ".join(result)


def switch_provider(new_prov):
    new_prov = str(new_prov).lower()
    if new_prov not in PROVIDERS:
        return
    old_p = str(cfg.get("provider", "rule34")).lower()
    cfg.setdefault("scores", {})[old_p] = cfg.get("min_score", 0)
    cfg["provider"] = new_prov
    cfg["min_score"] = cfg["scores"].get(new_prov, 0 if new_prov == "gelbooru" else 200)
    save_cfg()


def current_provider():
    p = str(cfg.get("provider", "rule34")).lower()
    return PROVIDERS.get(p, PROVIDERS["rule34"])


def api_posts(tags, limit=100, page=0):
    provider = current_provider()
    url = f"{provider['api_url']}?page=dapi&s=post&q=index&limit={limit}&pid={page}&tags={quote(tags)}{auth_query()}"
    root = ET.fromstring(get(url, timeout=20).content)
    return root


def normalize_tag(raw):
    tokens = [t.strip() for t in str(raw or "").split() if t.strip()]
    cleaned = []
    for token in tokens:
        tok = re.sub(r"(?<!_)\(", "_(", token)
        cleaned.append(tok)
    return " ".join(cleaned)


def read_history(folder):
    history = folder / ".history.txt"
    ids = set()
    if history.is_file():
        try:
            ids.update(line.strip() for line in history.read_text(encoding="utf-8").splitlines() if line.strip().isdigit())
        except OSError:
            pass
    if folder.is_dir():
        for file in folder.iterdir():
            match = re.match(r"(\d+)_score_", file.name)
            if file.is_file() and match:
                ids.add(match.group(1))
    return ids


def extract_post_info(post):
    post_id = post.get("id") or (post.findtext("id") if post.find("id") is not None else None)
    if post_id is not None:
        post_id = str(post_id).strip()
        if not post_id.isdigit():
            post_id = None
    url = post.get("file_url") or (post.findtext("file_url") if post.find("file_url") is not None else None)
    if not url:
        dir_val = post.get("directory") or (post.findtext("directory") if post.find("directory") is not None else None)
        img_val = post.get("image") or (post.findtext("image") if post.find("image") is not None else None)
        if dir_val and img_val:
            d_clean = re.sub(r'[^a-zA-Z0-9_-]', '', dir_val.strip())
            i_clean = re.sub(r'[^a-zA-Z0-9_.-]', '', img_val.strip())
            if d_clean and i_clean:
                url = f"https://img3.gelbooru.com/images/{d_clean}/{i_clean}"
    score_raw = post.get("score") or (post.findtext("score") if post.find("score") is not None else "0")
    score_str = str(score_raw).strip()
    score = score_str if re.match(r"^-?\d+$", score_str) else "0"
    return post_id, url, score


def download_one(item, folder, on_chunk=None):
    post_id, url, score = item
    extension = Path(urlsplit(url).path).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm"}:
        extension = ".jpg"
    target = folder / f"{post_id}_score_{score}{extension}"
    temporary = target.with_suffix(target.suffix + ".part")
    headers = dict(HEADERS)
    if "gelbooru.com" in url:
        headers["Referer"] = "https://gelbooru.com/"
    elif "rule34.xxx" in url:
        headers["Referer"] = "https://rule34.xxx/"
    try:
        with session().get(url, headers=headers, timeout=(10, 60), stream=True) as response:
            response.raise_for_status()
            with temporary.open("wb") as output:
                for block in response.iter_content(1024 * 64):
                    if block:
                        output.write(block)
                        if on_chunk:
                            on_chunk(len(block))
        if temporary.stat().st_size <= 512:
            temporary.unlink(missing_ok=True)
            return None
        temporary.replace(target)
        return post_id
    except (requests.RequestException, OSError):
        temporary.unlink(missing_ok=True)
        return None


def requested_limit(value, available):
    if str(value).lower() in ("all", "все"):
        return available
    try:
        return min(max(1, int(value)), available)
    except (TypeError, ValueError):
        return min(cfg["default_count"], available)


def download_tag(raw_tag, count, artist=False):
    tag = normalize_tag(raw_tag)
    if not tag:
        return
    provider = current_provider()
    sys.stdout.write(f"[*] {t('searching_api', provider=provider['name'])} \r")
    sys.stdout.flush()
    try:
        root = api_posts(f"{tag} {filters(tag)}", limit=1)
        sys.stdout.write(" " * 50 + "\r")
        sys.stdout.flush()
        if root.tag == "error":
            print(f"[-] {t('auth_required', provider=provider['name'])}")
            time.sleep(2)
            return
        total = int(root.get("count", "0"))
    except (requests.RequestException, ET.ParseError, ValueError):
        sys.stdout.write(" " * 50 + "\r")
        sys.stdout.flush()
        print(f"[-] {t('api_err', provider=provider['name'])}")
        if provider["name"] == "Gelbooru" and not (secret("gel_api_key") and secret("gel_user_id")):
            print(f"[*] {t('gelbooru_auth_hint')}")
        return
    if not total:
        if cfg.get("min_score", 0) > 0:
            try:
                base_check = api_posts(tag, limit=1)
                base_count = int(base_check.get("count", "0"))
                if base_count > 0:
                    print(f"[-] {t('no_posts_score', score=cfg['min_score'], count=base_count)}")
                    time.sleep(3)
                    return
            except Exception:
                pass
        print(f"[-] {t('no_posts')}")
        time.sleep(2)
        return

    franchise, character = resolve_paths(tag, artist)
    clean_stale_staging()
    staging = get_staging_dir()
    if staging.exists():
        print(f"[-] {t('staging_busy')}")
        return
    target_dir = staging / franchise / character
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        (staging / ".pid").write_text(f"{os.getpid()}:{int(time.time())}", encoding="utf-8")
    except Exception:
        pass
    archive = vault_path()
    failed_dump = None

    try:
        if archive.exists():
            sys.stdout.write(f"[*] {t('checking_vault', archive=archive.name)} \r")
            sys.stdout.flush()
            result = run_7z(["x", f"-p{vault_password()}", f"-o{staging}", "-r", "-y", "--", str(archive), f"{franchise}/{character}/*"])
            sys.stdout.write(" " * 55 + "\r")
            sys.stdout.flush()
            if result.returncode not in (0, 1):
                print(f"[-] {t('archive_open_error')}")
                return
        known = read_history(target_dir)
        tokens = tag.split()
        if len(tokens) == 1:
            available = max(0, total - len(known))
            limit = requested_limit(count, available)
        else:
            available = total
            limit = requested_limit(count, total)
        print(f"[*] {archive.name} -> {franchise}/{character}")
        print(f"[*] {t('stats_summary', total=total, known=len(known), available=available)}")
        if not limit:
            print(f"[*] {t('already_saved')}")
            time.sleep(2)
            return

        selected = []
        query = f"{tag} sort:score:desc {filters(tag)}"
        net_interrupted = False
        for page in range(0, 10001):
            sys.stdout.write(f"\r[*] {t('scanning_pages', page=page+1, count=len(selected), limit=limit)}  ")
            sys.stdout.flush()
            try:
                posts = api_posts(query, page=page).findall("post")
            except (requests.RequestException, ET.ParseError):
                net_interrupted = True
                break
            if not posts:
                break
            for post in posts:
                post_id, url, score = extract_post_info(post)
                if post_id and url and post_id not in known:
                    if url.startswith("//"):
                        url = "https:" + url
                    elif url.startswith("http://"):
                        url = "https://" + url[7:]
                    if urlsplit(url).scheme in ("https", "http"):
                        selected.append((post_id, url, score or "0"))
                        known.add(post_id)
                        if len(selected) == limit:
                            break
            if len(selected) == limit:
                break
        sys.stdout.write("\r" + " " * 65 + "\r")
        sys.stdout.flush()
        if net_interrupted:
            print(f"[!] {t('net_page_warning')}")
        if not selected:
            print(f"[-] {t('no_posts')}")
            time.sleep(2)
            return

        print(f"[*] {t('downloading')} {len(selected)} -> {franchise}/{character}...")
        completed = 0
        succeeded = []
        history_lock = threading.Lock()
        total_bytes = 0
        bytes_lock = threading.Lock()
        start_time = time.time()

        def on_chunk(n):
            nonlocal total_bytes
            with bytes_lock:
                total_bytes += n

        def progress():
            total_items = len(selected)
            percent = int(completed * 100 / total_items)
            width = int(20 * completed / total_items)
            bar = "█" * width + "░" * (20 - width)
            elapsed = max(0.001, time.time() - start_time)
            with bytes_lock:
                cur_b = total_bytes
            mb = cur_b / (1024 * 1024)
            mbps = (cur_b * 8) / (elapsed * 1_000_000)
            sys.stdout.write(f"\r  \033[36m[{bar}]\033[0m {percent:>3}% ({completed}/{total_items}) | {mb:.1f} MB | {mbps:.1f} Mbit/s  ")
            sys.stdout.flush()

        progress()
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(download_one, item, target_dir, on_chunk) for item in selected]
            for future in as_completed(futures):
                post_id = future.result()
                if post_id:
                    with history_lock:
                        succeeded.append(post_id)
                        with (target_dir / ".history.txt").open("a", encoding="utf-8") as history:
                            history.write(post_id + "\n")
                completed += 1
                progress()
        print()
        if not succeeded:
            print(f"[-] {t('download_failed')}")
            return

        with archive_lock, InterProcessLock(archive.with_suffix(".lock")):
            result = run_7z(
                ["a", f"-p{vault_password()}", "-mhe=on", "-mx0", "--", str(archive), f"./{franchise}"],
                cwd=staging,
            )
        if result.returncode != 0:
            failed_dump = staging.parent / f"_failed_{int(time.time())}"
            try:
                shutil.move(str(staging), str(failed_dump))
                dump_path = failed_dump
            except OSError:
                dump_path = staging
            print(f"[-] {t('archive_error', name=str(dump_path))}")
            return
        print(f"\033[32m[+] {t('vault_updated')}: {archive.stat().st_size / 1048576:.2f} MB\033[0m")
        print(f"[*] {t('download_success', done=len(succeeded), total=len(selected))}")
        time.sleep(2)
    finally:
        if failed_dump is None:
            shutil.rmtree(staging, ignore_errors=True)


def list_archive():
    archive = vault_path()
    if not archive.is_file():
        print(f"[*] {t('archive_empty', name=archive.name)}")
        return
    exe = seven_zip()
    if not exe:
        print(f"[-] {t('seven_zip_missing')}")
        return
    result = subprocess.run([exe, "l", "-slt", f"-p{vault_password()}", "--", str(archive)], capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        print(f"[-] {t('archive_read_error')}")
        return
    tree = {}
    for line in result.stdout.splitlines():
        if line.startswith("Path = "):
            parts = line[7:].strip().replace("\\", "/").split("/")
            if len(parts) >= 2 and not parts[-1].startswith("."):
                tree.setdefault(parts[0], set()).add(parts[1])
    print(f"\n=== {archive.name} ({archive.stat().st_size / 1048576:.2f} MB) ===")
    for franchise, folders in sorted(tree.items()):
        print(f"[{franchise}/]")
        for folder in sorted(folders):
            print(f"   └── {folder}")
    print()


def change_password():
    archive = vault_path()
    current = vault_password()
    if archive.exists():
        entered = getpass.getpass(t("current_password"))
        if entered != current:
            print(f"[-] {t('wrong_password')}")
            time.sleep(1.5)
            return
    new = getpass.getpass(t("new_password"))
    if not new:
        return
    if getpass.getpass(t("repeat_password")) != new:
        print(f"[-] {t('password_mismatch')}")
        time.sleep(1.5)
        return
    if archive.exists():
        with archive_lock, InterProcessLock(archive.with_suffix(".lock")):
            temporary = ROOT_DIR / "_rekey_tmp"
            shutil.rmtree(temporary, ignore_errors=True)
            temporary.mkdir(parents=True)
            try:
                result = run_7z(["x", f"-p{current}", f"-o{temporary}", "-y", "--", str(archive)])
                if result.returncode != 0:
                    print(f"[-] {t('password_unpack_error')}")
                    time.sleep(1.5)
                    return
                replacement = archive.with_suffix(".7z.new")
                replacement.unlink(missing_ok=True)
                result = run_7z(["a", f"-p{new}", "-mhe=on", "-mx0", "--", str(replacement), "*"], cwd=temporary)
                if result.returncode != 0:
                    replacement.unlink(missing_ok=True)
                    print(f"[-] {t('password_rekey_error')}")
                    time.sleep(1.5)
                    return
                os.replace(replacement, archive)
            finally:
                shutil.rmtree(temporary, ignore_errors=True)
    secrets["vault_pass"] = new
    save_cfg()
    print(f"[+] {t('password_changed')}")
    time.sleep(1)


def vault_settings():
    while True:
        clear_screen()
        print(f"\n{t('vault_title')}")
        print(f" 1. {t('vault_name')} : {vault_path().name}")
        pw_hint = f" ({t('pass_warn')})" if vault_password() == DEFAULT_PASSWORD else ""
        print(f" 2. {t('vault_pass')}    : {'*' * len(vault_password())}{pw_hint}")
        print(f" 3. {t('vault_pfx')}  : {cfg['folder_prefix']}\n 0. {t('cfg_back')}\n")
        choice = input("vault> ").strip()
        if choice == "1":
            name = input(t("name_prompt")).strip()
            if name:
                old = vault_path()
                cfg["vault_name"] = name.removesuffix(".7z")
                new = vault_path()
                if old.exists() and old != new:
                    old.rename(new)
                save_cfg()
        elif choice == "2":
            change_password()
        elif choice == "3":
            cfg["folder_prefix"] = safe_component(input(t("prefix_prompt")))[:5]
            save_cfg()
        elif choice.lower() in ("0", "q", "exit", "back"):
            return


def remove_tree(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def uninstall():
    clear_screen()
    program = Path(__file__).resolve()
    launchers = []
    if os.name != "nt" and os.environ.get("PREFIX"):
        bin_dir = Path(os.environ["PREFIX"]) / "bin"
        launchers.extend([bin_dir / "never", bin_dir / "r34"])
    elif os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        scripts_dir = Path(local_app) / "Programs" / "Scripts"
        launchers.extend([scripts_dir / "never.cmd", scripts_dir / "r34.cmd"])
    print(f"\n{t('uninstall_title')}\n{t('uninstall_warning')}\n")
    print(t("uninstall_paths", root=ROOT_DIR, config=CONFIG_PATH, program=program))
    if input(f"\n{t('uninstall_confirm')}").strip() != "DELETE":
        print(t("cancelled"))
        time.sleep(1)
        return False
    s_dir = get_staging_dir()
    targets = [ROOT_DIR, CONFIG_PATH, CONFIG_PATH.with_suffix(".tmp"), s_dir]
    try:
        targets.extend(s_dir.parent.glob("_failed_*"))
    except Exception:
        pass
    targets.extend(launchers)
    if os.name == "nt":
        targets.extend(program.with_name(f"{program.name}.{suffix}") for suffix in ("bak", "new", "newc"))
    for path in targets:
        try:
            remove_tree(path)
        except OSError:
            print(t("uninstall_error", path=path))
            time.sleep(2)
            return False
    print(t("uninstall_done"))
    if os.name == "nt":
        del_cmd = f'ping 127.0.0.1 -n 2 >nul & del /q "{program}"'
        if program.parent.name in ("NeverSearch", "umaZhickR34"):
            del_cmd += f' & rmdir /s /q "{program.parent}"'
        subprocess.Popen(["cmd", "/c", del_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        program.unlink(missing_ok=True)
    return True


def settings_menu():
    while True:
        clear_screen()
        prov_now = str(cfg.get("provider", "rule34")).lower()
        if prov_now == "gelbooru":
            hook = bool(secret("gel_api_key") and secret("gel_user_id"))
        else:
            hook = bool(secret("api_key") and secret("user_id"))
        hook_text = f"\033[32m{t('active')}\033[0m" if hook else f"\033[31m{t('offline')}\033[0m"
        src_label = current_provider()["name"]
        bl_status = t("on").upper() if cfg.get("filter_bl", True) else t("off").upper()
        bl_len = len(cfg.get("blacklist", []))
        v_mode_lbl = cfg.get("video_mode", "off").upper()
        print(f"\n{t('cfg_title')}")
        print(f" 1. {t('cfg_lang')}       : {cfg['lang']}")
        print(f" 2. {t('cfg_src')}   : {src_label} [r34 / gelbooru]")
        print(f" 3. {t('cfg_hook')}          : {hook_text}")
        print(f" 4. {t('cfg_vault')}")
        print(f" 5. {t('cfg_bl')}  : {bl_status} ({t('tags_count', count=bl_len)})")
        print(f" 6. {t('cfg_info')}")
        print(f" 7. {t('cfg_score')}        : {cfg['min_score']}")
        print(f" 8. {t('cfg_count')}    : {cfg['default_count']}")
        print(f" 9. {t('cfg_ai')}         : {t('on').upper() if cfg['filter_ai'] else t('off').upper()}")
        th_lbl = cfg.get('theme', 'blue').upper()
        print(f" 10. {t('cfg_video_mode')}        : {v_mode_lbl} [on / off / only]")
        print(f" 11. {t('cfg_theme')}  : {th_lbl} [mono / blue]")
        print(f" 12. {t('cfg_reset')}")
        print(f" 13. \033[31m{t('cfg_uninstall')}\033[0m")
        print(f" 0. {t('cfg_back')}\n")
        choice = input("cfg> ").strip()
        if choice == "1":
            language = input(t("lang_prompt")).strip().lower()
            if language in TEXT:
                cfg["lang"] = language
                save_cfg()
        elif choice == "2":
            new_src = "gelbooru" if cfg.get("provider") == "rule34" else "rule34"
            switch_provider(new_src)
            print(f"[+] {t('src_switched', name=PROVIDERS[new_src]['name'])} (score: {cfg['min_score']})")
            time.sleep(1)
        elif choice == "3":
            prov = current_provider()
            prov_name = prov["name"]
            is_gel = prov_name == "Gelbooru"
            k_key = "gel_api_key" if is_gel else "api_key"
            u_key = "gel_user_id" if is_gel else "user_id"
            raw = input(f"{prov_name} " + t("api_prompt")).strip()
            if raw.lower() in ("off", "0", "del"):
                secrets[k_key] = secrets[u_key] = ""
            else:
                key = re.search(r"api_key=([a-zA-Z0-9]+)", raw)
                user = re.search(r"user_id=([0-9]+)", raw)
                if key and user:
                    test_url = f"{prov['api_url']}?page=dapi&s=post&q=index&limit=1&api_key={key.group(1)}&user_id={user.group(1)}"
                    try:
                        test_res = requests.get(test_url, timeout=10)
                        if "<error>" in test_res.text:
                            print(f"[-] {t('api_rejected', provider=prov_name)}")
                            time.sleep(2)
                            continue
                    except requests.RequestException:
                        pass
                    secrets[k_key], secrets[u_key] = key.group(1), user.group(1)
                else:
                    print(f"[-] {t('bad_format')}")
                    time.sleep(1)
                    continue
            save_cfg()
        elif choice == "4":
            vault_settings()
        elif choice == "5":
            clear_screen()
            bl_list = cfg.get("blacklist", [])
            print(f"\n{t('bl_title')}")
            print(f"{t('bl_status_lbl')}: {t('on').upper() if cfg.get('filter_bl', True) else t('off').upper()}")
            tags_str = ', '.join(bl_list) if bl_list else t('bl_empty')
            print(f"{t('bl_current_tags', count=len(bl_list), tags=tags_str)}\n")
            print(f" 1. {t('bl_opt_toggle')}")
            print(f" 2. {t('bl_opt_add')}")
            print(f" 3. {t('bl_opt_del')}")
            print(f" 4. {t('bl_opt_clear')}")
            print(f" 0. {t('cfg_back')}\n")
            bl_c = input("bl> ").strip()
            if bl_c == "1":
                cfg["filter_bl"] = not cfg.get("filter_bl", True)
                save_cfg()
            elif bl_c == "2":
                tag_in = input(t("bl_prompt_add")).strip().replace(" ", "_")
                if tag_in and tag_in not in bl_list:
                    bl_list.append(tag_in)
                    cfg["blacklist"] = bl_list
                    save_cfg()
                    print(f"[+] {t('bl_added', tag=tag_in)}")
                    time.sleep(1)
            elif bl_c == "3":
                tag_rm = input(t("bl_prompt_del")).strip().replace(" ", "_")
                if tag_rm in bl_list:
                    bl_list.remove(tag_rm)
                    cfg["blacklist"] = bl_list
                    save_cfg()
                    print(f"[+] {t('bl_deleted', tag=tag_rm)}")
                    time.sleep(1)
            elif bl_c == "4":
                cfg["blacklist"] = []
                save_cfg()
                print(f"[+] {t('bl_cleared')}")
                time.sleep(1)
        elif choice == "6":
            show_info()
        elif choice in ("7", "8"):
            value = input(t("score_prompt" if choice == "7" else "count_prompt")).strip()
            if value.isdigit() and (choice == "7" or int(value) > 0):
                val_int = int(value)
                if choice == "7":
                    cfg["min_score"] = val_int
                    cfg.setdefault("scores", {})[cfg.get("provider", "rule34")] = val_int
                else:
                    cfg["default_count"] = val_int
                save_cfg()
        elif choice == "9":
            cfg["filter_ai"] = not cfg["filter_ai"]
            save_cfg()
        elif choice == "10":
            v_modes = ["off", "on", "only"]
            cur_m = cfg.get("video_mode", "off")
            idx = v_modes.index(cur_m) if cur_m in v_modes else 0
            new_m = v_modes[(idx + 1) % len(v_modes)]
            cfg["video_mode"] = new_m
            cfg["include_video"] = new_m in ("on", "only")
            save_cfg()
        elif choice == "11":
            new_th = "mono" if cfg.get("theme") == "blue" else "blue"
            cfg["theme"] = new_th
            save_cfg()
            print(f"[+] {t('theme_switched', name=new_th.upper())}")
            time.sleep(1)
        elif choice == "12":
            if input(t("reset_confirm")).strip().lower() != "y":
                print(t("cancelled"))
                time.sleep(1)
                continue
            language = cfg["lang"]
            kept_vault_name = cfg.get("vault_name", "Bible")
            kept_vault_pass = secret("vault_pass")
            cfg.clear()
            cfg.update({key: copy.deepcopy(value) for key, value in DEFAULTS.items() if key not in secrets})
            cfg["lang"] = language
            cfg["vault_name"] = kept_vault_name
            for key in secrets:
                secrets[key] = DEFAULTS[key]
            if kept_vault_pass:
                secrets["vault_pass"] = kept_vault_pass
            save_cfg()
            print(f"[+] {t('reset_done')}")
            time.sleep(1)
        elif choice == "13":
            if uninstall():
                raise SystemExit(0)
        elif choice.lower() in ("0", "q", "exit", "back"):
            return


class TagCompleter(Completer):
    def __init__(self):
        self.cache = {}

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        tokens = text.split()
        if not tokens:
            return
        command = tokens[0].lower()
        commands = {"score", "count", "clean", "clear", "cls", "exit", "quit", "q", "list", "set", "settings", "update", "info", "help", "man", "src", "source", "bl", "blacklist"}
        if command in commands:
            return
        if command == "video":
            if len(tokens) == 2:
                for option in ("on", "off", "only"):
                    if option.startswith(tokens[1].lower()):
                        yield Completion(option, start_position=-len(tokens[1]))
            return
        if command == "ai":
            if len(tokens) == 2:
                for option in ("on", "off"):
                    if option.startswith(tokens[1].lower()):
                        yield Completion(option, start_position=-len(tokens[1]))
            return
        if command in ("src", "source"):
            if len(tokens) == 2:
                for option in ("r34", "rule34", "gel", "gelbooru"):
                    if option.startswith(tokens[1].lower()):
                        yield Completion(option, start_position=-len(tokens[1]))
            return
        if command in ("bl", "blacklist"):
            if len(tokens) == 2:
                for option in ("on", "off", "add", "del", "list", "clear"):
                    if option.startswith(tokens[1].lower()):
                        yield Completion(option, start_position=-len(tokens[1]))
            return
        query = "" if text.endswith(" ") else tokens[-1].lower()
        if len(query) < 2:
            return
        if query not in self.cache:
            values = []
            provider = current_provider()
            try:
                if cfg.get("provider") == "gelbooru":
                    response = get(f"{provider['autocomplete_url']}&term={quote(query)}", timeout=2)
                else:
                    response = get(f"{provider['autocomplete_url']}?q={quote(query)}", timeout=2)
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            val = item.get("value") or item.get("label")
                            if val:
                                values.append((str(val), str(item.get("post_count", ""))))
                        elif isinstance(item, str):
                            values.append((item, ""))
            except (requests.RequestException, ValueError):
                pass
            self.cache[query] = values
        for value, count in self.cache[query][:10]:
            yield Completion(value, start_position=-len(query), display=value, display_meta=count)


def parse_query(parts):
    if parts[-1].isdigit():
        return " ".join(parts[:-1]), int(parts[-1])
    if parts[-1].lower() in ("all", "все"):
        return " ".join(parts[:-1]), "all"
    return " ".join(parts), cfg["default_count"]


def choose_language():
    if CONFIG_PATH.is_file():
        return
    clear_screen()
    print("\n  Select language / Выберите язык:\n")
    print("  1. Русский")
    print("  2. English\n")
    while True:
        choice = input("language> ").strip().lower()
        if choice in ("1", "ru", "русский"):
            cfg["lang"] = "ru"
            break
        if choice in ("2", "en", "english"):
            cfg["lang"] = "en"
            break
    print()
    while True:
        try:
            custom_pass = getpass.getpass(t("pass_prompt_init")).strip()
            if not custom_pass:
                if input(t("pass_default_confirm")).strip().lower() in ("y", "yes", "д", "да"):
                    secrets["vault_pass"] = DEFAULT_PASSWORD
                    print(f"[*] {t('pass_first_hint')}")
                    time.sleep(1.5)
                    break
                continue
            if len(custom_pass) < 4:
                print(f"[-] {t('pass_short')}")
                continue
            repeat = getpass.getpass(t("pass_repeat_init")).strip()
            if repeat != custom_pass:
                print(f"[-] {t('password_mismatch')}")
                continue
            secrets["vault_pass"] = custom_pass
            break
        except (KeyboardInterrupt, EOFError):
            break
    save_cfg()



def mask_credentials(text):
    text = str(text)
    text = re.sub(r"(api_key|user_id|token)=[^&\s'\"]+", r"\1=***", text)
    text = text.replace(str(Path.home()), "~")
    return text


def log_error(exc_text):
    try:
        log_path = CONFIG_PATH.with_name("error.log")
        if log_path.exists() and log_path.stat().st_size > 512 * 1024:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            log_path.write_text("\n".join(lines[-200:]) + "\n", encoding="utf-8")
        clean_text = mask_credentials(exc_text)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {clean_text}\n")
    except Exception:
        pass

def ensure_launcher_command():
    try:
        script_path = Path(__file__).resolve()
        if os.name != "nt":
            prefix = os.environ.get("PREFIX")
            if prefix:
                bin_dir = Path(prefix) / "bin"
                if bin_dir.is_dir():
                    sh_code = "#!/data/data/com.termux/files/usr/bin/bash\nexec python3 \"" + str(script_path) + "\" \"$@\"\n"
                    for cmd_name in ("never", "r34"):
                        launcher = bin_dir / cmd_name
                        launcher.write_text(sh_code, encoding="utf-8")
                        try:
                            launcher.chmod(0o755)
                        except OSError:
                            pass
        else:
            local_app = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
            scripts_dir = Path(local_app) / "Programs" / "Scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            py_exe = sys.executable
            batch_lines = [
                "@echo off",
                "chcp 65001 >nul",
                "set PYTHONUTF8=1",
                f'if exist "{py_exe}" (',
                f'    "{py_exe}" "{script_path}" %*',
                ") else (",
                f'    py -3 "{script_path}" %* 2>nul || python "{script_path}" %*',
                ")",
                ""
            ]
            batch_code = "\r\n".join(batch_lines)
            for cmd_name in ("never.cmd", "r34.cmd"):
                target_cmd = scripts_dir / cmd_name
                target_cmd.write_text(batch_code, encoding="utf-8")
            here_cmd = script_path.with_name("never.cmd")
            if not here_cmd.exists():
                here_cmd.write_text(batch_code, encoding="utf-8")
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                    val, typ = winreg.QueryValueEx(key, "Path")
                    parts = [p.strip() for p in val.split(";") if p.strip()]
                    s_str = str(scripts_dir)
                    if s_str not in parts:
                        winreg.SetValueEx(key, "Path", 0, typ, f"{s_str};{val}")
            except Exception:
                pass
    except Exception:
        pass


def main():
    if not sys.stdin.isatty():
        print(t("interactive_only"))
        return 1
    global ROOT_DIR
    try:
        ROOT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        fallback = Path.home() / "Documents" / "NeverSearch"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            ROOT_DIR = fallback
        except OSError:
            ROOT_DIR = Path.home() / "NeverSearch"
            try:
                ROOT_DIR.mkdir(parents=True, exist_ok=True)
            except OSError:
                print(t("storage_denied", path=ROOT_DIR, error=error))
                if os.name != "nt":
                    print(t("storage_hint"))
                return 1
    choose_language()
    ensure_system_dependencies()
    ensure_launcher_command()
    check_auto_update(silent=True)
    print_banner()
    completer = ThreadedCompleter(TagCompleter())
    while True:
        try:
            line = prompt([("class:prompt", "NeverSearch> ")], completer=completer, complete_while_typing=True, style=STYLE).strip()
            if not line:
                continue
            parts = line.split()
            command = parts[0].lower()
            if command in ("exit", "quit", "q", "выход"):
                print(t("shutdown"))
                return 0
            if command in ("info", "help", "man", "инфо", "справка"):
                show_info()
            elif command == "theme":
                if len(parts) > 1 and parts[1].lower() in ("mono", "blue"):
                    cfg["theme"] = parts[1].lower()
                else:
                    cfg["theme"] = "mono" if cfg.get("theme") == "blue" else "blue"
                save_cfg()
                print(f"[+] {t('theme_set', theme=cfg['theme'].upper())}")
                time.sleep(1)
            elif command == "update":
                check_auto_update(silent=False)
            elif command in ("set", "settings"): 
                settings_menu()
            elif command in ("clear", "cls"):
                pass
            elif command == "list":
                list_archive()
                input("[Enter] ")
            elif command == "score" and len(parts) == 2 and parts[1].isdigit():
                new_s = int(parts[1])
                cfg["min_score"] = new_s
                cfg.setdefault("scores", {})[cfg.get("provider", "rule34")] = new_s
                save_cfg()
            elif command == "count" and len(parts) == 2 and parts[1].isdigit() and int(parts[1]) > 0:
                cfg["default_count"] = int(parts[1])
                save_cfg()
            elif command == "video" and len(parts) >= 2:
                v_arg = parts[1].lower()
                if v_arg in ("only", "2"):
                    cfg["video_mode"] = "only"
                    cfg["include_video"] = True
                elif v_arg in ("on", "1", "true"):
                    cfg["video_mode"] = "on"
                    cfg["include_video"] = True
                else:
                    cfg["video_mode"] = "off"
                    cfg["include_video"] = False
                save_cfg()
                print(f"[+] {t('video_mode_set', mode=cfg['video_mode'].upper())}")
                time.sleep(1)
            elif command == "ai" and len(parts) >= 2:
                cfg["filter_ai"] = parts[1].lower() in ("on", "1", "true")
                save_cfg()
            elif command in ("src", "source", "booru"):
                if len(parts) > 1:
                    src_arg = parts[1].lower()
                    target_p = "gelbooru" if src_arg in ("gel", "gelbooru") else "rule34"
                else:
                    target_p = "gelbooru" if cfg.get("provider") == "rule34" else "rule34"
                switch_provider(target_p)
                print(f"[+] {t('source_set', source=current_provider()['name'], score=cfg['min_score'])}")
                time.sleep(1)
            elif command in ("bl", "blacklist"):
                bl_data = cfg.get("blacklist", [])
                if len(parts) == 1 or parts[1].lower() == "list":
                    state = t("on").upper() if cfg.get("filter_bl", True) else t("off").upper()
                    print(f"[*] {t('bl_list_hdr', state=state, tags=', '.join(bl_data) if bl_data else t('bl_empty'))}")
                    time.sleep(2)
                elif len(parts) >= 2:
                    sub = parts[1].lower()
                    if sub in ("on", "1"):
                        cfg["filter_bl"] = True
                        save_cfg()
                        print(f"[+] {t('bl_set', status=t('on').upper())}")
                    elif sub in ("off", "0"):
                        cfg["filter_bl"] = False
                        save_cfg()
                        print(f"[+] {t('bl_set', status=t('off').upper())}")
                    elif sub == "add" and len(parts) > 2:
                        for item_t in parts[2:]:
                            c_tag = item_t.strip().replace(" ", "_")
                            if c_tag and c_tag not in bl_data:
                                bl_data.append(c_tag)
                        cfg["blacklist"] = bl_data
                        save_cfg()
                        print(f"[+] {t('bl_updated', tags=', '.join(bl_data) if bl_data else t('bl_empty'))}")
                    elif sub in ("del", "rm", "remove") and len(parts) > 2:
                        for item_t in parts[2:]:
                            c_tag = item_t.strip().replace(" ", "_")
                            if c_tag in bl_data:
                                bl_data.remove(c_tag)
                        cfg["blacklist"] = bl_data
                        save_cfg()
                        print(f"[+] {t('bl_updated', tags=', '.join(bl_data) if bl_data else t('bl_empty'))}")
                    elif sub == "clear":
                        cfg["blacklist"] = []
                        save_cfg()
                        print(f"[+] {t('bl_cleared')}")
                    time.sleep(1)
            elif command == "artist" and len(parts) > 1:
                name, count = parse_query(parts[1:])
                if name:
                    download_tag(name, count, artist=True)
            elif command == "clean" and len(parts) == 2 and parts[1].lower() in ("all", "все"):
                answer = input(t("clean_confirm_all", root=ROOT_DIR)).strip()
                if answer == "DELETE":
                    for item in ROOT_DIR.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    print(f"[+] {t('clean_purged')}")
                    time.sleep(1)
                else:
                    print(f"[-] {t('cancelled')}")
                    time.sleep(1)
            else:
                name, count = parse_query(parts)
                download_tag(name, count)
            print_banner()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{t('shutdown')}")
            return 0
        except Exception as error:
            log_error(traceback.format_exc())
            print(f"[-] Error: {mask_credentials(error)}")
            time.sleep(2)
            print_banner()


if __name__ == "__main__":
    raise SystemExit(main())
