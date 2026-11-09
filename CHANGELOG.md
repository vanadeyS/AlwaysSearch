# Changelog

All notable changes to the **NeverSearch** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.05.08] - 2026-11-10

### Added
- **GitHub Actions CI (`.github/workflows/ci.yml`)**: automated testing across Python 3.10, 3.11, and 3.12 with `pyflakes` linting and `pytest`.
- **Linter & Lock Test Suite**: added `test_inter_process_lock` and `test_no_undefined_variables_linter` to verify zero undefined symbols across codebase.

### Fixed
- **Missing `import errno`**: added missing `import errno` to imports header, eliminating potential `NameError` on lock fallbacks.
- **Immediate `.pid` Marker**: `staging.mkdir()` now writes `.pid` immediately before subfolder creation, closing any race condition window.
- **Unused Imports Cleaned**: removed unused `random` import and redundant global declarations (verified 0 pyflakes warnings).
- **README Phrasing**: balanced source guarantee descriptions.

---

## [1.05.07] - 2026-11-10

### Fixed
- **NameError in Lock Resolver**:
  - Fixed `get_vault_lock_path()` referencing nonexistent `vault_name()` helper instead of reading config key `cfg.get("vault_name", "Bible")`.
  - Canonical LF SHA-256 manifest hash calculation in deployer.

---

## [1.05.06] - 2026-11-10

### Fixed
- **FUSE / Android Storage Locking**:
  - Moved `.lock` file from external storage (`/storage/emulated/0/...`) to local ext4 directory (`~/.Bible.lock` on Termux / `%LOCALAPPDATA%` on Windows).
  - Added graceful fallback for filesystems lacking POSIX `flock` support (`ENOSYS`, `EOPNOTSUPP`, `EINVAL`), preventing false 30-second `TimeoutError` hangs.
- **Stale Staging Lock in Same Process**:
  - Fixed `clean_stale_staging()` to automatically purge leftover `_staging` directories belonging to the current process (`pid == os.getpid()`), eliminating false "Another process is already using _staging" blocks after interrupted downloads.
- **Windows Installer Compatibility**:
  - `install_windows.ps1` now strictly validates Python 3.8+ via `Test-ValidPython3` and ignores bundled ancient Python 2.7 from OpenOffice, LibreOffice, and GIMP.
  - Safe error handling in PowerShell during dependency installation (`ensurepip` stderr suppression).

---

## [1.05.05] - 2026-11-09

### Added
- **Vault Password UX**:
  - Removed insecure default password on initial startup.
  - Added cryptographic Diceware password generator (`word-word-word-pin` format using standard `secrets` module, e.g. `frost-tiger-orbit-7429`) offering 40+ bits of entropy with human readability.
  - Added menu option `3. Показать текущий пароль` (`Show current password`) in Vault settings (`set -> 2 -> 3`) with one-key clipboard copying (`[c]` via Windows `clip` / Termux `termux-clipboard-set`).
  - Added centralized `export_password_backup()` helper creating `vault_password_backup.txt` (default prompt changed to `y/N`, POSIX permissions `0o600`).
  - Automatic synchronization of `vault_password_backup.txt` on password change (`change_password`).
- **OTA Integrity Check**:
  - Added strict SHA-256 integrity verification (`r34_gallery.py.sha256`) during OTA update. Aborts update with clear error if manifest is unreachable, corrupt, or digest mismatches.
- **Unit Test Suite**:
  - Added test suite in `tests/test_core.py` (8/8 tests passed) covering `safe_component`, `normalize_tag`, `requested_limit`, `parse_version`, `resolve_paths`, Diceware password generator, SHA-256 verification, and repo hash synchronization.
  - Fully compatible with standard stdlib `unittest` and `pytest`.
  - Import-safe: deferred `install_python_dependencies` to runtime `main()`, avoiding subprocess `pip` execution during test imports.
- **Security Guide**:
  - Added bilingual `SECURITY.md` (Русский + English) documenting encryption architecture, DPAPI, and threat model.

### Fixed
- Fixed backslash escaping in `safe_component` regex character class preventing path traversal on Windows.
- Clean exit (`sys.exit(0)`) on `Ctrl+C` interrupt during initial vault setup.

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
