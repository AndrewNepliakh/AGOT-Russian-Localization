# A Game of Thrones: The Board Game — Russian Localization

Русификатор для **A Game of Thrones: The Board Game – Digital Edition (Steam)**.

## Установка

1. Распакуйте архив `AGoT_RU_x64.zip`.
2. Откройте **Steam → Библиотека → A Game of Thrones: The Board Game → Управление → Просмотреть локальные файлы**.
3. Скопируйте `AGoT_RU.exe` в папку игры, рядом с `AGameOfThronesTheBoardGame.exe`.
4. Запустите `AGoT_RU.exe`.
5. Дождитесь сообщения об успешной установке.

Пример расположения:

```text
C:\Program Files (x86)\Steam\steamapps\common\A Game of Thrones The Board Game\
├── AGameOfThronesTheBoardGame.exe
├── AGameOfThronesTheBoardGame_Data\
└── AGoT_RU.exe
```

**Важно:** русификатор устанавливается на оригинальную, неизменённую версию игры.

## Восстановление оригинальной игры

1. Откройте CMD в папке игры.
2. Выполните:

```cmd
AGoT_RU.exe --restore
```

Оригинальные файлы будут восстановлены из папки `RussianLocalization_Backup`, а файлы русификатора удалены.

**Не удаляйте `RussianLocalization_Backup` до восстановления игры.**

## Требования

- Windows 10/11 (64-bit).
- Оригинальная Steam-версия игры.
- Дополнительные программы не требуются.

## Возможные ошибки

- **Поместите AGoT_RU.exe рядом с AGameOfThronesTheBoardGame.exe** — установщик находится не в папке игры.
- **Патч не подходит к версии игры** — файлы игры отличаются от поддерживаемой версии.
- **Резервная копия уже существует** — русификатор уже устанавливался. Сначала восстановите оригинальные файлы через `--restore`.

## Ссылки

Исходный код и обновления: https://github.com/AndrewNepliakh/AGOT-Russian-Localization

*Неофициальная фанатская локализация. Проект не связан с разработчиками и издателем игры.*