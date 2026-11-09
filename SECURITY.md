# Security Policy / Политика безопасности

[ 🇷🇺 Русский ](#-русский) | [ 🇬🇧 English ](#-english)

---

<a id="-русский"></a>
## 🇷🇺 Русский

### Поддерживаемые версии

| Версия  | Поддержка          |
| ------- | ------------------ |
| 1.05.x  | :white_check_mark: |
| < 1.05  | :x:                |

### Архитектура безопасности и модель угроз

NeverSearch спроектирован как автономная консольная утилита с минимальным набором проверенных зависимостей (`requests`, `prompt_toolkit`, `7-Zip`):

1. **Шифрование хранилища (AES-256)**:
   - Все медиафайлы упаковываются в зашифрованный контейнер 7-Zip (`Bible.7z`).
   - Используется алгоритм AES-256 с обязательным шифрованием заголовков (`-mhe=on`). Без знания пароля невозможно просмотреть даже список файлов, их имена или размеры.
   - Загруженные файлы собираются во временном каталоге (`_staging`), пакуются в архив и удаляются с диска стандартными средствами ОС (`shutil.rmtree`).
   - Атомарная перешифровка: при смене пароля создаётся временный архив (`.7z.new`), и только после успешной упаковки он подменяет старый файл.

2. **Защита учётных данных и паролей**:
   - **Windows**: Пароль архива и API-токены шифруются системным механизмом Windows DPAPI (`CryptProtectData`). Другие учётные записи Windows не имеют доступа к расшифровке.
   - **Android / Linux (Termux)**: Файл конфигурации сохраняется с правами доступа `0o600` (чтение и запись только владельцу процесса).

3. **Проверка целостности обновлений (OTA SHA-256)**:
   - При выполнении команды `update` скачанный код сверяется с цифровым отпечатком `r34_gallery.py.sha256`. Если хеш не совпадает или манифест повреждён, обновление прерывается, а рабочий файл остаётся нетронутым.

4. **Ограничения и рекомендации**:
   - **Видимость процессов в ОС**: При упаковке через 7-Zip аргумент `-p<пароль>` передаётся через CLI. На многопользовательских shared-серверах это теоретически может быть видно другим локальным пользователям через `ps`. На персональных ПК (Windows) и смартфонах (Termux) процессы изолированы контекстом пользователя.
   - **Памятка пароля**: Посмотреть текущий пароль можно в консоли через меню `set` -> пункт 2 (`Показать текущий пароль`, клавиша `c` копирует в буфер обмена). При экспорте `vault_password_backup.txt` храните его вне облачных папок (OneDrive).

---

<a id="-english"></a>
## 🇬🇧 English

### Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.05.x  | :white_check_mark: |
| < 1.05  | :x:                |

### Security Architecture & Threat Model

NeverSearch is designed as a standalone client with minimal verified dependencies (`requests`, `prompt_toolkit`, `7-Zip`):

1. **Vault Encryption (AES-256)**:
   - Media files are compressed and stored inside an encrypted 7-Zip container (`Bible.7z`).
   - Uses AES-256 with header encryption enabled (`-mhe=on`). Without the password, directory structure, file names, and file sizes are completely invisible to external inspection.
   - Temporary files are processed in a local staging directory (`_staging`), packed, and removed via OS filesystem cleanup (`shutil.rmtree`).
   - Atomic re-keying: Changing the vault password writes to a replacement archive (`.7z.new`) and swaps it with the primary archive only upon verified success.

2. **Credential Protection**:
   - **Windows**: API tokens and vault passwords in `~/.r34_config.json` are encrypted using Windows Data Protection API (**DPAPI** via `CryptProtectData`). Only processes running under the same user session can decrypt them.
   - **Android / Linux (Termux)**: Config files are saved with restrictive POSIX permissions (`chmod 0o600`), readable only by the owning user process.

3. **OTA Update Verification (SHA-256)**:
   - Updates downloaded via the `update` command or automatic checks are verified against a standalone `r34_gallery.py.sha256` checksum prior to compilation and execution.
   - If payload signature or SHA-256 digest fails, the update is rejected and the existing executable remains untouched.

4. **Known Boundaries**:
   - **Local Process Visibility**: On shared multi-user Unix machines, process arguments (e.g. 7-Zip CLI arguments during brief archive runs) may be visible to other local processes via `ps`. On single-user Android (Termux) and Windows, this is bounded by user session isolation.
   - **Password Backups**: If you export `vault_password_backup.txt`, store it in a secure location or delete it once memorized.

---

## Reporting a Vulnerability / Сообщить об уязвимости

If you discover a security vulnerability or design flaw, please report it privately:
- Contact: **vanadeyS** via GitHub Issues or pull requests.
- Responsible disclosure is appreciated and will be credited in release notes.
