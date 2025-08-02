#!/usr/bin/env python3
"""
Планировщик для автоматического запуска Union Build автоматизации
Поддерживает различные режимы работы и гибкое расписание
"""

import schedule
import time
import threading
import logging
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Callable
import subprocess
import sys
import os

from advanced_automation import AdvancedUnionBuildAutomation

class UnionBuildScheduler:
    """Планировщик для автоматизации Union Build"""
    
    def __init__(self, config_file: str = "scheduler_config.json"):
        self.config = self._load_scheduler_config(config_file)
        self.setup_logging()
        self.is_running = False
        self.current_job = None
        self.job_history = []
        
    def _load_scheduler_config(self, config_file: str) -> Dict:
        """Загрузка конфигурации планировщика"""
        default_config = {
            "schedule_mode": "random",  # fixed, random, intervals
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
            "min_interval_between_sessions": 120,  # минуты
            "max_sessions_per_day": 5,
            "enable_weekends": True,
            "enable_weekdays": True,
            "skip_dates": [],  # даты в формате "YYYY-MM-DD"
            "retry_failed_sessions": True,
            "max_retry_attempts": 2,
            "notification": {
                "enabled": False,
                "webhook_url": "",
                "telegram_bot_token": "",
                "telegram_chat_id": ""
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Ошибка загрузки конфига планировщика: {e}")
        
        return default_config
    
    def setup_logging(self):
        """Настройка логирования планировщика"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduler.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('UnionBuildScheduler')
    
    def should_run_today(self) -> bool:
        """Проверка, должен ли планировщик работать сегодня"""
        today = datetime.now()
        
        # Проверка выходных/будней
        is_weekend = today.weekday() >= 5
        if is_weekend and not self.config.get("enable_weekends", True):
            return False
        if not is_weekend and not self.config.get("enable_weekdays", True):
            return False
        
        # Проверка пропускаемых дат
        today_str = today.strftime("%Y-%m-%d")
        if today_str in self.config.get("skip_dates", []):
            return False
        
        return True
    
    def get_sessions_today(self) -> int:
        """Получение количества сессий сегодня"""
        today = datetime.now().date()
        return len([job for job in self.job_history 
                   if job['date'].date() == today])
    
    def can_schedule_more_sessions(self) -> bool:
        """Проверка возможности планирования дополнительных сессий"""
        sessions_today = self.get_sessions_today()
        max_sessions = self.config.get("max_sessions_per_day", 5)
        return sessions_today < max_sessions
    
    def run_automation_job(self):
        """Запуск задания автоматизации"""
        if not self.should_run_today():
            self.logger.info("Сегодня планировщик не должен работать")
            return
        
        if not self.can_schedule_more_sessions():
            self.logger.info("Достигнуто максимальное количество сессий на сегодня")
            return
        
        # Проверка минимального интервала
        if not self._check_minimum_interval():
            self.logger.info("Не прошел минимальный интервал между сессиями")
            return
        
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Запуск задания {job_id}")
        
        job_info = {
            'id': job_id,
            'date': datetime.now(),
            'status': 'running',
            'attempts': 1,
            'result': None,
            'error': None
        }
        
        try:
            # Запуск автоматизации
            automation = AdvancedUnionBuildAutomation()
            success = automation.run_automation_with_recovery()
            
            job_info['status'] = 'completed' if success else 'failed'
            job_info['result'] = success
            
            if success:
                self.logger.info(f"Задание {job_id} выполнено успешно")
                self._send_notification(f"✅ Задание {job_id} выполнено успешно")
            else:
                self.logger.error(f"Задание {job_id} завершилось с ошибкой")
                self._handle_failed_job(job_info)
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения задания {job_id}: {e}")
            job_info['status'] = 'error'
            job_info['error'] = str(e)
            self._handle_failed_job(job_info)
        
        finally:
            self.job_history.append(job_info)
            self._cleanup_old_history()
    
    def _check_minimum_interval(self) -> bool:
        """Проверка минимального интервала между сессиями"""
        if not self.job_history:
            return True
        
        last_job = max(self.job_history, key=lambda x: x['date'])
        min_interval = timedelta(minutes=self.config.get("min_interval_between_sessions", 120))
        
        return datetime.now() - last_job['date'] >= min_interval
    
    def _handle_failed_job(self, job_info: Dict):
        """Обработка неудачного задания"""
        if not self.config.get("retry_failed_sessions", True):
            return
        
        max_attempts = self.config.get("max_retry_attempts", 2)
        if job_info['attempts'] >= max_attempts:
            self.logger.error(f"Исчерпаны попытки для задания {job_info['id']}")
            self._send_notification(f"❌ Задание {job_info['id']} провалено после {max_attempts} попыток")
            return
        
        # Планируем повторную попытку через случайное время (30-60 минут)
        retry_delay = random.randint(30, 60)
        self.logger.info(f"Планируется повторная попытка через {retry_delay} минут")
        
        def retry_job():
            time.sleep(retry_delay * 60)
            job_info['attempts'] += 1
            job_info['status'] = 'retrying'
            self.run_automation_job()
        
        retry_thread = threading.Thread(target=retry_job)
        retry_thread.daemon = True
        retry_thread.start()
    
    def _send_notification(self, message: str):
        """Отправка уведомления"""
        if not self.config.get("notification", {}).get("enabled", False):
            return
        
        try:
            # Telegram уведомления
            telegram_config = self.config["notification"]
            if telegram_config.get("telegram_bot_token") and telegram_config.get("telegram_chat_id"):
                self._send_telegram_notification(message, telegram_config)
            
            # Webhook уведомления
            if telegram_config.get("webhook_url"):
                self._send_webhook_notification(message, telegram_config["webhook_url"])
                
        except Exception as e:
            self.logger.error(f"Ошибка отправки уведомления: {e}")
    
    def _send_telegram_notification(self, message: str, config: Dict):
        """Отправка Telegram уведомления"""
        import requests
        
        url = f"https://api.telegram.org/bot{config['telegram_bot_token']}/sendMessage"
        data = {
            'chat_id': config['telegram_chat_id'],
            'text': f"🤖 Union Build Bot\n\n{message}",
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            self.logger.info("Telegram уведомление отправлено")
        else:
            self.logger.error(f"Ошибка отправки Telegram: {response.status_code}")
    
    def _send_webhook_notification(self, message: str, webhook_url: str):
        """Отправка webhook уведомления"""
        import requests
        
        data = {
            'text': message,
            'timestamp': datetime.now().isoformat(),
            'source': 'union_build_automation'
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        if response.status_code == 200:
            self.logger.info("Webhook уведомление отправлено")
        else:
            self.logger.error(f"Ошибка отправки webhook: {response.status_code}")
    
    def _cleanup_old_history(self):
        """Очистка старой истории заданий"""
        # Оставляем только записи за последние 7 дней
        cutoff_date = datetime.now() - timedelta(days=7)
        self.job_history = [job for job in self.job_history 
                           if job['date'] > cutoff_date]
    
    def setup_fixed_schedule(self):
        """Настройка фиксированного расписания"""
        times = self.config.get("fixed_times", ["09:00", "15:00", "21:00"])
        
        for time_str in times:
            schedule.every().day.at(time_str).do(self.run_automation_job)
            self.logger.info(f"Запланирована сессия на {time_str}")
    
    def setup_random_schedule(self):
        """Настройка случайного расписания"""
        sessions_per_day = self.config.get("random_sessions_per_day", 3)
        time_range = self.config.get("random_time_range", {"start": "08:00", "end": "22:00"})
        
        def schedule_random_session():
            if not self.can_schedule_more_sessions():
                return
            
            start_hour, start_minute = map(int, time_range["start"].split(":"))
            end_hour, end_minute = map(int, time_range["end"].split(":"))
            
            # Генерируем случайное время
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            random_minutes = random.randint(start_minutes, end_minutes)
            
            hour = random_minutes // 60
            minute = random_minutes % 60
            
            time_str = f"{hour:02d}:{minute:02d}"
            
            schedule.every().day.at(time_str).do(self.run_automation_job).tag('random')
            self.logger.info(f"Запланирована случайная сессия на {time_str}")
        
        # Планируем случайные сессии на день
        for _ in range(sessions_per_day):
            schedule_random_session()
        
        # Каждый день в полночь планируем новые случайные сессии
        def reset_random_schedule():
            schedule.clear('random')
            for _ in range(sessions_per_day):
                schedule_random_session()
        
        schedule.every().day.at("00:01").do(reset_random_schedule)
    
    def setup_interval_schedule(self):
        """Настройка интервального расписания"""
        interval_config = self.config.get("interval_mode", {"hours": 4, "random_offset_minutes": 30})
        base_hours = interval_config.get("hours", 4)
        random_offset = interval_config.get("random_offset_minutes", 30)
        
        def schedule_next_interval():
            # Добавляем случайное смещение к базовому интервалу
            offset_minutes = random.randint(-random_offset, random_offset)
            total_minutes = base_hours * 60 + offset_minutes
            
            next_run = datetime.now() + timedelta(minutes=total_minutes)
            
            schedule.every().day.at(next_run.strftime("%H:%M")).do(
                lambda: [self.run_automation_job(), schedule_next_interval()]
            ).tag('interval')
            
            self.logger.info(f"Следующая интервальная сессия запланирована на {next_run.strftime('%H:%M')}")
        
        # Запускаем первый интервал
        schedule_next_interval()
    
    def start_scheduler(self):
        """Запуск планировщика"""
        self.logger.info("Запуск планировщика Union Build")
        
        # Настройка расписания в зависимости от режима
        mode = self.config.get("schedule_mode", "random")
        
        if mode == "fixed":
            self.setup_fixed_schedule()
        elif mode == "random":
            self.setup_random_schedule()
        elif mode == "intervals":
            self.setup_interval_schedule()
        else:
            self.logger.error(f"Неизвестный режим планировщика: {mode}")
            return
        
        self.is_running = True
        self._send_notification("🚀 Планировщик Union Build запущен")
        
        # Основной цикл планировщика
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
                
        except KeyboardInterrupt:
            self.logger.info("Получен сигнал остановки")
        except Exception as e:
            self.logger.error(f"Ошибка в планировщике: {e}")
        finally:
            self.stop_scheduler()
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.logger.info("Остановка планировщика")
        self.is_running = False
        schedule.clear()
        self._send_notification("⏹️ Планировщик Union Build остановлен")
    
    def get_status(self) -> Dict:
        """Получение статуса планировщика"""
        return {
            'is_running': self.is_running,
            'next_jobs': [str(job) for job in schedule.jobs],
            'sessions_today': self.get_sessions_today(),
            'total_jobs_in_history': len(self.job_history),
            'last_job': self.job_history[-1] if self.job_history else None
        }

def create_scheduler_config():
    """Создание примера конфигурации планировщика"""
    config = {
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
    
    with open("scheduler_config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("Создан файл scheduler_config.json с примером конфигурации")

def main():
    """Главная функция планировщика"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Union Build Scheduler')
    parser.add_argument('--create-config', action='store_true', 
                       help='Создать пример конфигурации')
    parser.add_argument('--status', action='store_true', 
                       help='Показать статус планировщика')
    parser.add_argument('--config', default='scheduler_config.json',
                       help='Путь к файлу конфигурации')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_scheduler_config()
        return
    
    scheduler = UnionBuildScheduler(args.config)
    
    if args.status:
        status = scheduler.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
        return
    
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        print("\nПолучен сигнал остановки")
        scheduler.stop_scheduler()

if __name__ == "__main__":
    main()