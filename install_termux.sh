#!/data/data/com.termux/files/usr/bin/bash
set -e

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME="${HOME:-/data/data/com.termux/files/home}"
TARGET="$HOME/r34_gallery.py"
LAUNCHER="$PREFIX/bin/never"
LAUNCHER_R34="$PREFIX/bin/r34"

SYS_LANG="${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}"
if [[ "$SYS_LANG" =~ ^(ru|be|uk) ]]; then
    MSG_START="[*] Загрузка NeverSearch (r34_gallery.py)..."
    MSG_DONE="\n\033[32m[+] Установка завершена. Запуск NeverSearch...\033[0m\n"
else
    MSG_START="[*] Downloading NeverSearch (r34_gallery.py)..."
    MSG_DONE="\n\033[32m[+] Installation complete. Starting NeverSearch...\033[0m\n"
fi

mkdir -p "$PREFIX/bin"

if command -v pkg >/dev/null 2>&1; then
    DEBIAN_FRONTEND=noninteractive apt-get update -y 2>/dev/null || pkg update -y 2>/dev/null || true
    pkg install -y python 7zip curl
elif command -v apt-get >/dev/null 2>&1; then
    DEBIAN_FRONTEND=noninteractive apt-get update -y 2>/dev/null || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip p7zip-full curl
fi

python3 -m pip install --upgrade requests prompt_toolkit --break-system-packages 2>/dev/null || \
python3 -m pip install --upgrade requests prompt_toolkit --user 2>/dev/null || \
python3 -m pip install --upgrade requests prompt_toolkit 2>/dev/null || true

printf '%s\n' "$MSG_START"
curl -fL "https://raw.githubusercontent.com/vanadeyS/umaZhickR34/main/r34_gallery.py" -o "$TARGET"

cat << 'EOF' > "$LAUNCHER"
#!/data/data/com.termux/files/usr/bin/sh
exec python3 "$HOME/r34_gallery.py" "$@"
EOF

cp "$LAUNCHER" "$LAUNCHER_R34"
chmod 755 "$TARGET" "$LAUNCHER" "$LAUNCHER_R34"
python3 -m py_compile "$TARGET" 2>/dev/null || true

if [ ! -d "$HOME/storage" ] && command -v termux-setup-storage >/dev/null 2>&1; then
    termux-setup-storage 2>/dev/null || true
fi

printf "$MSG_DONE"
if [ -t 0 ]; then
    exec python3 "$TARGET" "$@"
elif [ -e /dev/tty ]; then
    exec python3 "$TARGET" "$@" < /dev/tty
else
    exec python3 "$TARGET" "$@"
fi
