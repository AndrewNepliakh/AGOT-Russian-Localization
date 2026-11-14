# AGoT_RU — Rider project

Сохранены оригинальная иконка и имя EXE. Установщик использует актуальный `generated_files.json`, 3 xdelta-патча и 2 новых файла (или любой будущий набор из манифеста).

1. Распакуйте папку `AGoT_RU` рядом с `AGOT-Russian-Localization` (в `steamapps\common`).
2. Откройте `AGoT_RU.csproj` в Rider.
3. В терминале Rider выполните `powershell -ExecutionPolicy Bypass -File .\build.ps1`.
4. Готовый `publish\AGoT_RU.exe` скопируйте в папку игры рядом с `AGameOfThronesTheBoardGame.exe`.
5. Запустите EXE, подтвердите установку. Для восстановления: `AGoT_RU.exe --restore` из CMD.

Сборка берёт патчи из соседней папки `AGOT-Russian-Localization`, а `xdelta3.exe` из `C:\Tools\xdelta3\xdelta3.exe`. Никаких ручных списков файлов в C# нет. Пользователю .NET и xdelta3 устанавливать не нужно.

Не запускайте установщик на уже локализованной игре. При несовпадении исходных файлов xdelta проверка завершится ошибкой до записи. После установки сохраняется `RussianLocalization_Backup`.
