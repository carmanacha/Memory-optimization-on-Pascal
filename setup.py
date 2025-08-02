#!/usr/bin/env python3
"""
Установочный скрипт для Union Build Automation
Автоматически настраивает окружение и создает начальные конфигурации
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path

def print_banner():
    """Печать баннера"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                   Union Build Automation                     ║
║                      Setup Script                           ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Ваша версия: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python версия: {sys.version.split()[0]}")

def install_requirements():
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def check_chrome():
    """Проверка установки Chrome"""
    print("\n🌐 Проверка браузера Chrome...")
    
    chrome_paths = {
        'Windows': [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        'Darwin': [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ],
        'Linux': [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
    }
    
    system = platform.system()
    paths = chrome_paths.get(system, [])
    
    for path in paths:
        if os.path.exists(path):
            print(f"✅ Chrome найден: {path}")
            return True
    
    print("⚠️  Chrome не найден. Пожалуйста, установите Google Chrome")
    print("Скачать: https://www.google.com/chrome/")
    return False

def create_config_files():
    """Создание конфигурационных файлов"""
    print("\n⚙️  Создание конфигурационных файлов...")
    
    # Основная конфигурация
    config = {
        "min_delay": 60,
        "max_delay": 300,
        "transaction_amount_min": 0.001,
        "transaction_amount_max": 0.01,
        "headless": False,
        "implicit_wait": 15,
        "page_load_timeout": 45,
        "networks_to_use": [
            "ethereum",
            "arbitrum",
            "polygon",
            "cosmos",
            "osmosis"
        ],
        "max_transactions_per_session": 3,
        "wallet_passwords": {
            "metamask": "",
            "keplr": ""
        },
        "chrome_profile_path": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "proxy": {
            "enabled": False,
            "host": "",
            "port": "",
            "username": "",
            "password": ""
        },
        "retry_attempts": 3,
        "screenshot_on_error": True
    }
    
    # Конфигурация планировщика
    scheduler_config = {
        "schedule_mode": "random",
        "fixed_times": ["09:00", "15:00", "21:00"],
        "random_sessions_per_day": 3,
        "random_time_range": {
            "start": "08:00",
            "end": "22:00"
        },
        "interval_mode": {
            "hours": 4,
            "random_offset_minutes": 30
        },
        "min_interval_between_sessions": 120,
        "max_sessions_per_day": 5,
        "enable_weekends": True,
        "enable_weekdays": True,
        "skip_dates": [],
        "retry_failed_sessions": True,
        "max_retry_attempts": 2,
        "notification": {
            "enabled": False,
            "webhook_url": "",
            "telegram_bot_token": "",
            "telegram_chat_id": ""
        }
    }
    
    # Сохранение конфигураций
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    with open("scheduler_config.json", 'w', encoding='utf-8') as f:
        json.dump(scheduler_config, f, indent=2, ensure_ascii=False)
    
    print("✅ Конфигурационные файлы созданы:")
    print("   - config.json")
    print("   - scheduler_config.json")

def create_directories():
    """Создание необходимых директорий"""
    print("\n📁 Создание директорий...")
    
    directories = ["logs", "screenshots", "data"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Создана директория: {directory}/")

def create_run_scripts():
    """Создание скриптов запуска"""
    print("\n📜 Создание скриптов запуска...")
    
    # Windows batch файл
    if platform.system() == "Windows":
        with open("run_automation.bat", 'w') as f:
            f.write("""@echo off
echo Starting Union Build Automation...
python advanced_automation.py
pause
""")
        
        with open("run_scheduler.bat", 'w') as f:
            f.write("""@echo off
echo Starting Union Build Scheduler...
python scheduler.py
pause
""")
        print("✅ Созданы Windows скрипты:")
        print("   - run_automation.bat")
        print("   - run_scheduler.bat")
    
    # Unix shell скрипты
    else:
        with open("run_automation.sh", 'w') as f:
            f.write("""#!/bin/bash
echo "Starting Union Build Automation..."
python3 advanced_automation.py
""")
        
        with open("run_scheduler.sh", 'w') as f:
            f.write("""#!/bin/bash
echo "Starting Union Build Scheduler..."
python3 scheduler.py
""")
        
        # Делаем скрипты исполняемыми
        os.chmod("run_automation.sh", 0o755)
        os.chmod("run_scheduler.sh", 0o755)
        
        print("✅ Созданы Unix скрипты:")
        print("   - run_automation.sh")
        print("   - run_scheduler.sh")

def setup_git_hooks():
    """Настройка git hooks (если это git репозиторий)"""
    if os.path.exists(".git"):
        print("\n🔧 Настройка git hooks...")
        
        pre_commit_hook = """#!/bin/sh
# Проверка синтаксиса Python файлов
python -m py_compile *.py
if [ $? -ne 0 ]; then
    echo "❌ Ошибка синтаксиса в Python файлах"
    exit 1
fi
echo "✅ Синтаксис Python файлов корректен"
"""
        
        hooks_dir = Path(".git/hooks")
        hooks_dir.mkdir(exist_ok=True)
        
        with open(hooks_dir / "pre-commit", 'w') as f:
            f.write(pre_commit_hook)
        
        os.chmod(hooks_dir / "pre-commit", 0o755)
        print("✅ Git hooks настроены")

def print_next_steps():
    """Печать следующих шагов"""
    print("\n" + "="*60)
    print("🎉 Установка завершена успешно!")
    print("="*60)
    
    print("\n📋 Следующие шаги:")
    print("1. Отредактируйте config.json под свои нужды")
    print("2. Настройте кошельки MetaMask и Keplr в браузере")
    print("3. При необходимости настройте уведомления в scheduler_config.json")
    
    print("\n🚀 Запуск:")
    if platform.system() == "Windows":
        print("   Одиночный запуск: run_automation.bat")
        print("   Планировщик:      run_scheduler.bat")
    else:
        print("   Одиночный запуск: ./run_automation.sh")
        print("   Планировщик:      ./run_scheduler.sh")
    
    print("\n📖 Документация: README.md")
    
    print("\n⚠️  Важные напоминания:")
    print("   - Используйте малые суммы для тестирования")
    print("   - Регулярно проверяйте логи и транзакции")
    print("   - Автоматизация может нарушать условия сервиса")
    print("   - Используйте на свой страх и риск")

def main():
    """Главная функция установки"""
    print_banner()
    
    print("🔍 Проверка системы...")
    check_python_version()
    chrome_ok = check_chrome()
    
    if not chrome_ok:
        response = input("\nПродолжить без Chrome? (y/N): ")
        if response.lower() != 'y':
            print("Установка прервана. Установите Chrome и запустите снова.")
            sys.exit(1)
    
    # Установка зависимостей
    if not install_requirements():
        print("\n❌ Не удалось установить зависимости")
        print("Попробуйте установить вручную: pip install -r requirements.txt")
        sys.exit(1)
    
    # Создание файлов и директорий
    create_config_files()
    create_directories()
    create_run_scripts()
    setup_git_hooks()
    
    # Финальные инструкции
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка установки: {e}")
        sys.exit(1)