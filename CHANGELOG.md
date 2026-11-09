# Changelog

All notable changes to the **NeverSearch** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.05.05] - 2026-11-09

### Added
- **Vault Password UX**:
  - Removed insecure default password on initial startup.
  - Added simple memorable password generator (`word-number` format, e.g. `star-449`, `tiger-197`) that is easy to remember and mistype-resistant.
  - Added menu option `3. Показать текущий пароль` (`Show current password`) in Vault settings (`set -> 2 -> 3`).
  - Added menu option `4. Экспорт пароля в файл` (`Export password to file`) in Vault settings (`set -> 2 -> 4`) generating `vault_password_backup.txt`.
  - Automatic synchronization of `vault_password_backup.txt` on password change (`change_password`).
- **OTA Integrity Check**:
  - Added SHA-256 integrity verification (`r34_gallery.py.sha256`) during OTA update before applying or compiling updates.
- **Unit Test Suite**:
  - Added test suite in `tests/test_core.py` covering core pure functions (`safe_component`, `normalize_tag`, `requested_limit`, `parse_version`, `resolve_paths`, `generate_simple_password`, and `sha256_verification`).
  - Compatible with standard stdlib `unittest` and `pytest`.
- **CI / GitHub Actions**:
  - Added `.github/workflows/ci.yml` running unit tests and linting across Python 3.10, 3.11, and 3.12.
- **Security Guide**:
  - Added `SECURITY.md` documenting encryption boundaries and credential safety.

### Fixed
- Fixed backslash escaping in `safe_component` regex character class preventing path traversal on Windows.

---

## [1.05.04] - 2026-11-09

### Changed
- Replaced legacy Umamusume references in banners, examples, and manuals with popular franchises (Genshin Impact, Zenless Zone Zero).
- Explicit `clean all` warning: clearly specifies that the entire folder including the encrypted archive will be deleted.
- Merged config saving preserving admin keys on normal saves, full wipe on settings reset (`save_cfg(merge=False)`).
- Upgraded `admin_push.py` with Git Data Blobs API to support binary screenshot uploads.
- Dynamic tag version badge in README pointing to official repository tags.

---

## [1.05.03] - 2026-11-08

### Added
- Tag autocomplete via `prompt_toolkit` on both Rule34 and Gelbooru APIs.
- Blacklist manager (`bl on/off/add/del/list/clear`) with instant persistence.
- Automatic franchise sorting: detects franchise tags (e.g. `_(genshin_impact)`) and creates organized subfolders inside the vault.

---

## [1.05.02] - 2026-11-07

### Added
- Video downloading modes: `video off` (images only), `video on` (images and videos), `video only` (strictly MP4/WebM).
- Dual color themes: `blue` (cyan-accented cyberpunk header) and `mono` (clean monochrome).

---

## [1.05.01] - 2026-11-06

### Added
- Gelbooru API integration alongside Rule34.
- Independent score filtering and API Hook configuration per provider.

---

## [1.05.00] - 2026-11-05

### Added
- 7-Zip AES-256 header-encrypted vault storage (`-mhe=on`).
- Windows DPAPI credential protection (`CryptProtectData`).
- POSIX permissions protection on Termux (`chmod 0o600`).
- Atomic re-keying and staging directory cleanup.

---

## [1.00.00] - 2026-10-18

### Added
- Initial standalone release of NeverSearch CLI client.
