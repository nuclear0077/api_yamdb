## API-YAMDB

## About
API для backend Yatube.

## Technology
Python 3.7, Django 3.2, DRF 3.12, Simplejwt,SQLite

## Documentation

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/nuclear0077/api_final_yatube
```

```
cd api_final_yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Создать супер пользователя:

```
python manage.py createsuperuser
```

Запустить проект:

```
python3 manage.py runserver
```

### Документация API.
Для просмотра документации необходимо запустить проект и перейти по ссылке http://localhost:8000/redoc/
или перейти https://editor.swagger.io нажать на file, выбрать import url и в поле указать https://github.com/nuclear0077/api_final_yatube/blob/master/yatube_api/static/redoc.yaml

## Developer

- [Aleksandr M](https://github.com/nuclear0077)
- Telegram @nuclear0077

