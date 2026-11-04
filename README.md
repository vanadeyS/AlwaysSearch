# umaZhickR34

Локальный клиент Rule34 с шифрованным хранилищем 7z для Windows и Termux.

## Windows

Выполните в командной строке или PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://gist.githubusercontent.com/vanadeyS/fd557488cadf0371fb235876bb85c9f2/raw/install_windows.ps1 | iex"; r34
```

Установщик загружает актуальную версию, Python-библиотеки и 7-Zip. После установки программа запускается командой `r34`. Если команда не находится, закройте и снова откройте терминал.

## Termux

```bash
pkg install -y curl && curl -fL https://gist.githubusercontent.com/vanadeyS/fd557488cadf0371fb235876bb85c9f2/raw/install_termux.sh -o ~/install_termux.sh && bash ~/install_termux.sh && r34
```

Дальнейший запуск:

```bash
r34
```

## Обновления

Программа проверяет обновления при запуске. Ручная проверка — команда `update` внутри программы.

Файлы и настройки хранятся локально. Архив на Windows: `Документы\umaZhickR34\Bible.7z`; на Android: `Documents/umaZhickR34/Bible.7z`.
