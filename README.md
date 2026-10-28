# Тетрис

Standalone desktop Tetris game built with Python and Pygame.  
Ported from the original web-based HTML version into a native application that runs without a browser.

---

## Скачать в один клик   
[tetris.exe](https://github.com/zgammer/tetris-for-boring-lessons/releases/download/1.0.0app/tetris.exe)   
[tetris_1.0.0_amd64.deb](https://github.com/zgammer/tetris-for-boring-lessons/releases/download/1.0.0app/tetris_1.0.0_amd64.deb)

---

## Управление

Управление работает **независимо от раскладки клавиатуры** (используются скан-коды физических клавиш).

| Действие            | Клавиши              |
|---------------------|----------------------|
| Движение влево      | `←` или `A`          |
| Движение вправо     | `→` или `D`          |
| Поворот             | `↑` или `W`          |
| Ускорить падение    | `↓` или `S`          |
| Сбросить вниз       | `Space`              |
| Пауза               | `P` или `Esc`        |
| Новая игра          | `R`                  |
| Звук вкл./выкл.     | `M`                  |

---

## Запуск из исходников

### Требования

- Python 3.9+
- pip

### Установка и запуск

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить игру
python tetris.py
```

---

## Сборка для Windows (.exe)

### Требования

- Python 3.9+
- pip

### Шаги

```bash
# 1. Установить зависимости
python -m pip install -r requirements.txt

# 2. Собрать .exe (один файл, без консоли)
python -m PyInstaller --onefile --noconsole --name tetris tetris.py
```

Готовый файл `tetris.exe` появится в папке `dist/`.

> **Примечание:** Если папка `Scripts` Python не добавлена в PATH, вызов через `python -m PyInstaller` гарантирует запуск без ошибок `CommandNotFoundException`.  
> Можно также собрать через spec-файл:
> ```bash
> python -m PyInstaller tetris.spec
> ```

---

## Сборка для Linux (.deb)

### Требования

- Python 3.9+
- python3-venv
- dpkg-deb
- SDL2 (`libsdl2-2.0-0`, `libsdl2-mixer-2.0-0`)

### Вариант 1: Автоматическая сборка скриптом

```bash
chmod +x build_deb.sh
./build_deb.sh
```

Скрипт создаст `.deb`-пакет в папке `dist/`.

### Вариант 2: Ручная сборка

```bash
# 1. Создать и активировать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Собрать бинарник
pyinstaller --onefile --noconsole --name tetris tetris.py

# 4. Установить бинарник или собрать пакет .deb вручную
# (см. build_deb.sh для структуры пакета)

deactivate
```

### Установка .deb пакета

```bash
sudo dpkg -i dist/tetris_1.0.0_amd64.deb
```

После установки игра запускается командой `tetris` или через меню приложений.

---

## Структура проекта

```
├── tetris.py          # Основной код игры (Python + Pygame)
├── requirements.txt   # Зависимости Python
├── tetris.spec        # PyInstaller spec-файл
├── build_deb.sh       # Скрипт сборки .deb пакета для Linux
├── index.html         # Оригинальная веб-версия (HTML)
└── README.md          # Этот файл
```
