# API заказов и промокодов

Django-проект с REST API для создания заказов, применением промокодов и импортом email-рассылок из XLSX-файлов через отложенные Celery-задачи.

## Стек

- Python 3.10+
- Django 4.2+
- Django REST Framework
- Celery
- openpyxl
- SQLite

## Структура проекта

- `shop` - каталог товаров, категории, заказы, позиции заказа и API создания заказа.
- `marketing` - промокоды, история использования промокодов, импорт рассылок и Celery-задачи отправки email-сообщений.
- `fixtures` - тестовые данные и пример XLSX-файла для импорта рассылок.
- `config` - настройки Django и Celery.

## Локальный запуск

Создайте и активируйте виртуальное окружение:

```bash
python -m venv env
```

Linux/macOS:

```bash
source env/bin/activate
```

Windows PowerShell:

```powershell
.\env\Scripts\Activate.ps1
```

Установите зависимости и подготовьте базу данных:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata fixtures/test_data.json
python manage.py runserver
```

После запуска API будет доступен по адресу:

```text
http://127.0.0.1:8000/
```

## Тестовые данные

Фикстура `fixtures/test_data.json` создает:

- пользователей: `customer` с `user_id=1`, `second_customer` с `user_id=2`;
- товары: `Django Book` с `good_id=1`, `Laptop` с `good_id=2`, `Board Game` с `good_id=3`;
- промокоды: `SUMMER2025`, `BOOKS10`, `EXPIRED`, `LIMIT`.

Особенности тестовых данных:

- `SUMMER2025` дает скидку 10% на все товары, кроме исключенных из акций.
- `BOOKS10` дает скидку 10% только на товары категории `Books`.
- `EXPIRED` просрочен.
- `LIMIT` уже достиг лимита использований.
- `Laptop` исключен из промоакций.

## API создания заказа

Создание заказа:

```http
POST /api/v1/orders/
Content-Type: application/json
```

Поле `promo_code` необязательное.

Пример запроса:

```json
{
  "user_id": 1,
  "goods": [
    {
      "good_id": 1,
      "quantity": 2
    }
  ],
  "promo_code": "SUMMER2025"
}
```

Пример ответа:

```json
{
  "user_id": 1,
  "order_id": 1,
  "goods": [
    {
      "good_id": 1,
      "quantity": 2,
      "price": 100,
      "discount": "0.1",
      "total": 180
    }
  ],
  "price": 200,
  "discount": "0.1",
  "total": 180
}
```

Пример запроса через `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "goods": [
      {
        "good_id": 1,
        "quantity": 2
      }
    ],
    "promo_code": "SUMMER2025"
  }'
```

## Правила применения промокодов

- Промокод должен существовать.
- Промокод должен быть активным.
- Промокод не должен быть просрочен или запланирован на будущее.
- У промокода есть общий лимит использований.
- Один пользователь может использовать один промокод только один раз.
- Промокод может быть ограничен определенными категориями товаров.
- Товары, исключенные из акций, не получают скидку.

## Импорт рассылок из XLSX

Приложение `marketing` поддерживает импорт email-рассылок из XLSX-файлов с последующей отложенной отправкой через Celery.

Первая строка файла должна содержать заголовки колонок:

| Колонка | Описание |
| --- | --- |
| `external_id` | уникальный идентификатор записи во внешней системе |
| `user_id` | идентификатор пользователя |
| `email` | email получателя |
| `subject` | тема письма |
| `message` | текст письма |

`external_id` используется для идемпотентности: если файл импортировать повторно, уже обработанные строки не будут созданы заново.

Файл читается потоково через `openpyxl` в режиме `read_only=True`, поэтому большие XLSX-файлы не загружаются полностью в оперативную память.

## Тестовый XLSX-файл

В проекте есть пример файла:

```text
fixtures/mailings_import_sample.xlsx
```

В нем 5 строк данных:

- 2 валидные строки;
- 1 дубль `external_id`, который должен попасть в пропущенные записи;
- 1 строка с некорректным email;
- 1 строка с несуществующим `user_id`.

## Запуск импорта рассылок

Сначала примените миграции и загрузите тестовые данные:

```bash
python manage.py migrate
python manage.py loaddata fixtures/test_data.json
```

В первом терминале запустите Celery worker:

```bash
celery -A config worker -l info --pool=solo
```

Во втором терминале запустите импорт:

```bash
python manage.py import_mailings fixtures/mailings_import_sample.xlsx --countdown 5
```

Ожидаемый результат первого запуска:

```text
Processed rows: 5
Created records: 2
Skipped records: 1
Error rows: 2
```

Через 5 секунд Celery worker запишет отправку писем в лог. Для упрощения задачи реальная отправка email не выполняется: Celery-задача логирует сообщение и помечает запись как отправленную.

Повторный запуск того же файла должен показать, что уже импортированные `external_id` не создаются повторно.

## Настройки Celery

По умолчанию проект использует локальный filesystem broker Celery и создает служебные папки в `celery_broker/`.

Для production-like окружения можно переопределить broker через переменные окружения:

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

На Windows локальный filesystem broker требует пакет `pywin32`. Он уже добавлен в `requirements.txt` с Windows-only marker.

Задержка отправки по умолчанию задается переменной:

```bash
MARKETING_EMAIL_SEND_DELAY_SECONDS=5
```

Также задержку можно передать при запуске команды:

```bash
python manage.py import_mailings fixtures/mailings_import_sample.xlsx --countdown 10
```

## Тесты

Запуск тестов:

```bash
python manage.py test
```

Проверка синхронизации миграций:

```bash
python manage.py makemigrations --check --dry-run
```
