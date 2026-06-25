# API заказов с промокодами

Django REST Framework проект для создания заказов с опциональным применением промокода.

## Стек

- Python 3.10+
- Django 4.2+
- Django REST Framework
- SQLite

## Структура проекта

- `shop` - категории, товары, заказы, позиции заказа, API создания заказа и сервис расчёта стоимости.
- `marketing` - промокоды и история их использования пользователями, в дальнейшем сюда можно будет добавить реферальную программу, систему бонусов, баллов и .д.
- `fixtures` - тестовые данные для локального запуска.

## Локальный запуск

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py loaddata fixtures/test_data.json
python3 manage.py runserver
```

## Тестовые данные

Фикстура `fixtures/test_data.json` создаёт:

- пользователей: `customer` с `user_id=1`, `second_customer` с `user_id=2`;
- товары: `Django Book` с `good_id=1`, `Laptop` с `good_id=2`, `Board Game` с `good_id=3`;
- промокоды: `SUMMER2025`, `BOOKS10`, `EXPIRED`, `LIMIT`.

Особенности тестовых данных:

- `SUMMER2025` даёт скидку 10% на все товары, кроме исключённых из акций.
- `BOOKS10` даёт скидку 10% только на категорию `Books`.
- `EXPIRED` просрочен.
- `LIMIT` уже достиг лимита использований.
- `Laptop` исключён из любых акций.

## API

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

Пример запроса через `curl` для Windows PowerShell:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":1,\"goods\":[{\"good_id\":1,\"quantity\":2}],\"promo_code\":\"SUMMER2025\"}"
```

## Правила применения промокода

- Промокод должен существовать.
- Промокод должен быть активным.
- Промокод не должен быть просрочен или запланирован на будущее.
- У промокода есть общий лимит использований.
- Один пользователь может использовать один промокод только один раз.
- Промокод может быть ограничен определёнными категориями товаров.
- Товары, исключённые из акций, никогда не получают скидку.

## Проверки

Запуск тестов:

```bash
python3 manage.py test
```

Проверка синхронизации моделей и миграций:

```bash
python3 manage.py makemigrations --check --dry-run
```
