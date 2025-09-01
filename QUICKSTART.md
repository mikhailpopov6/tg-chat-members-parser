# 🚀 Quick Start Guide

## Быстрый запуск за 5 минут

### 1. Установка
```bash
git clone <your-repo-url>
cd tg-paerser-members-chat
pip install -r requirements.txt
```

### 2. Настройка API ключей
```bash
cp config_local.py.example config_local.py
```

Отредактируйте `config_local.py`:
```python
API_ID = 'your_api_id_here'          # Получить на https://my.telegram.org/apps
API_HASH = 'your_api_hash_here'      # Получить на https://my.telegram.org/apps
PHONE_NUMBER = '+79001234567'        # Ваш номер телефона с кодом страны
GROUP_LINK = 'https://t.me/channel'  # Ссылка на канал для парсинга
```

### 3. Запуск
```bash
python telegram_members_parser_prod.py
```

### 4. Результат
- Файл с участниками: `telegram_members_complete_YYYYMMDD_HHMMSS.xlsx`
- Логи: `telegram_parser.log`

## ⚠️ Важно

- **НЕ коммитьте** файл `config_local.py` в Git!
- Убедитесь, что вы **администратор** канала
- Ожидайте **96%+ покрытие** участников канала

## 🆘 Проблемы?

1. **Ошибка авторизации** → Проверьте API_ID, API_HASH, PHONE_NUMBER
2. **Канал не найден** → Убедитесь, что вы админ канала
3. **Мало участников** → Проверьте права доступа в канале

Подробная документация: [README.md](README.md)
