# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.05.x  | :white_check_mark: |
| < 1.05  | :x:                |

---

## Security Architecture & Threat Model

NeverSearch is designed as a standalone, zero-dependency client with strong local data privacy:

### 1. Vault Encryption (AES-256)
- Media files are compressed and stored inside an encrypted 7-Zip container (`Bible.7z`).
- Uses AES-256 with header encryption enabled (`-mhe=on`). Without the password, directory structure, file names, and file sizes are completely invisible to external inspection.
- Temporary files are processed in a local staging directory (`_staging`), packed, and securely wiped after archival.
- Atomic re-keying: Changing the vault password writes to a replacement archive (`.7z.new`) and swaps it with the primary archive only upon verified success.

### 2. Credential Protection
- **Windows**: API tokens and vault passwords in `~/.r34_config.json` are encrypted using Windows Data Protection API (**DPAPI** via `CryptProtectData`). Only processes running under the same user session can decrypt them.
- **Android / Linux (Termux)**: Config files are saved with restrictive POSIX permissions (`chmod 0o600`), readable only by the owning user process.

### 3. OTA Update Verification
- Updates downloaded via the `update` command or automatic checks are verified against a standalone `r34_gallery.py.sha256` checksum prior to compilation and execution.
- If payload signature or SHA-256 digest fails, the update is rejected and the existing executable remains untouched.

### 4. Known Boundaries
- **Local Process Visibility**: On shared multi-user Unix machines, process arguments (e.g. 7-Zip CLI arguments during brief archive runs) may be visible to other local processes via `ps`. On single-user Android (Termux) and Windows, this is bounded by user session isolation.
- **Password Backups**: If you export `vault_password_backup.txt`, store it in a secure location or delete it once memorized.

---

## Reporting a Vulnerability

If you discover a security vulnerability or design flaw, please report it privately:
- Contact: **vanadeyS** via GitHub Issues (with private flag) or pull requests.
- Responsible disclosure is appreciated and will be credited in release notes.
