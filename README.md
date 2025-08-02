# Union Build Automation

Автоматизированный скрипт для работы с платформой Union Build, который автоматически подключает EVM и Cosmos кошельки и выполняет случайные bridge транзакции между различными сетями.

## 🚀 Возможности

- **Автоматическое подключение кошельков**: MetaMask (EVM) и Keplr (Cosmos)
- **Случайные транзакции**: Автоматическое выполнение bridge операций между сетями
- **Гибкое расписание**: Поддержка фиксированного, случайного и интервального планирования
- **Обход защиты**: Использование undetected-chrome для обхода антибот систем
- **Уведомления**: Telegram и webhook уведомления о статусе работы
- **Восстановление**: Автоматические повторные попытки при ошибках
- **Логирование**: Подробные логи всех операций

## 📋 Поддерживаемые сети

### EVM сети:
- Ethereum Mainnet
- Arbitrum One
- Polygon
- BSC (Binance Smart Chain)

### Cosmos сети:
- Cosmos Hub
- Osmosis
- Juno

## ⚙️ Установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd union-build-automation
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Установка Chrome/Chromium
Убедитесь, что у вас установлен Google Chrome или Chromium браузер.

### 4. Настройка расширений кошельков
- Установите MetaMask в браузере
- Установите Keplr в браузере
- Настройте кошельки и добавьте нужные сети

## 🔧 Конфигурация

### Основная конфигурация (config.json)

```json
{
  "min_delay": 60,
  "max_delay": 300,
  "transaction_amount_min": 0.001,
  "transaction_amount_max": 0.01,
  "headless": false,
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
  "retry_attempts": 3,
  "screenshot_on_error": true
}
```

### Конфигурация планировщика (scheduler_config.json)

```json
{
  "schedule_mode": "random",
  "random_sessions_per_day": 3,
  "random_time_range": {
    "start": "08:00", 
    "end": "22:00"
  },
  "min_interval_between_sessions": 120,
  "max_sessions_per_day": 5,
  "enable_weekends": true,
  "enable_weekdays": true,
  "notification": {
    "enabled": false,
    "telegram_bot_token": "",
    "telegram_chat_id": ""
  }
}
```

## 🚀 Использование

### Одиночный запуск

#### Базовая версия:
```bash
python union_build_automation.py
```

#### Расширенная версия (рекомендуется):
```bash
python advanced_automation.py
```

### Планировщик

#### Создание конфигурации планировщика:
```bash
python scheduler.py --create-config
```

#### Запуск планировщика:
```bash
python scheduler.py
```

#### Проверка статуса:
```bash
python scheduler.py --status
```

## 📝 Режимы планировщика

### 1. Фиксированное расписание
```json
{
  "schedule_mode": "fixed",
  "fixed_times": ["09:00", "15:00", "21:00"]
}
```

### 2. Случайное расписание
```json
{
  "schedule_mode": "random",
  "random_sessions_per_day": 3,
  "random_time_range": {
    "start": "08:00",
    "end": "22:00"
  }
}
```

### 3. Интервальное расписание
```json
{
  "schedule_mode": "intervals",
  "interval_mode": {
    "hours": 4,
    "random_offset_minutes": 30
  }
}
```

## 🔔 Настройка уведомлений

### Telegram уведомления

1. Создайте бота через @BotFather
2. Получите токен бота
3. Найдите свой chat_id
4. Обновите конфигурацию:

```json
{
  "notification": {
    "enabled": true,
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID"
  }
}
```

### Webhook уведомления

```json
{
  "notification": {
    "enabled": true,
    "webhook_url": "https://your-webhook-url.com/endpoint"
  }
}
```

## 📊 Мониторинг

### Логи
- `union_build_automation.log` - основные логи автоматизации
- `scheduler.log` - логи планировщика
- Скриншоты ошибок сохраняются автоматически

### Файлы логов содержат:
- Время выполнения операций
- Детали подключения кошельков
- Информацию о транзакциях
- Ошибки и предупреждения
- Статистику сессий

## ⚠️ Важные замечания

### Безопасность
- Никогда не делитесь своими seed фразами или приватными ключами
- Используйте отдельные кошельки для автоматизации
- Регулярно проверяйте баланс и транзакции

### Риски
- Автоматизация может нарушать условия использования платформы
- Возможны потери средств из-за ошибок или сбоев в сети
- Комиссии сети могут превышать суммы транзакций

### Рекомендации
- Начните с малых сумм для тестирования
- Регулярно проверяйте работу скрипта
- Используйте тестовые сети для отладки
- Не оставляйте большие суммы в автоматизированных кошельках

## 🛠️ Структура проекта

```
union-build-automation/
├── union_build_automation.py    # Базовый скрипт автоматизации
├── advanced_automation.py       # Расширенная версия с улучшениями
├── scheduler.py                 # Планировщик заданий
├── config.json                  # Основная конфигурация
├── scheduler_config.json        # Конфигурация планировщика
├── requirements.txt             # Зависимости Python
├── README.md                    # Документация
└── logs/                        # Папка с логами (создается автоматически)
```

## 🔧 Продвинутые настройки

### Прокси
```json
{
  "proxy": {
    "enabled": true,
    "host": "proxy.example.com",
    "port": "8080",
    "username": "user",
    "password": "pass"
  }
}
```

### Пользовательский агент
```json
{
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### Профиль Chrome
```json
{
  "chrome_profile_path": "/path/to/chrome/profile"
}
```

## 🐛 Устранение неполадок

### Частые проблемы:

1. **ChromeDriver не найден**
   - Убедитесь, что Chrome установлен
   - Обновите chromedriver

2. **Кошелек не подключается**
   - Проверьте установку расширений
   - Убедитесь, что кошельки разблокированы

3. **Элементы не найдены**
   - Сайт мог измениться
   - Проверьте селекторы в коде

4. **Ошибки сети**
   - Проверьте интернет-соединение
   - Убедитесь, что RPC узлы доступны

### Отладка:
```bash
# Запуск с видимым браузером
python advanced_automation.py

# Проверка логов
tail -f union_build_automation.log
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для фичи
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

Этот проект предназначен для образовательных целей. Использование на свой страх и риск.

## ⚡ Быстрый старт

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте базовую конфигурацию:
```bash
python scheduler.py --create-config
```

3. Отредактируйте `config.json` под свои нужды

4. Запустите тест:
```bash
python advanced_automation.py
```

5. Запустите планировщик:
```bash
python scheduler.py
```

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте логи на наличие ошибок
2. Убедитесь, что конфигурация корректна
3. Попробуйте запустить в режиме отладки
4. Создайте issue с описанием проблемы

---

**Осторожно**: Автоматизация может нарушать условия использования сервисов. Используйте на свой страх и риск.