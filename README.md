EDX-ejudge-grader
===============

Серверное приложение для проверки решений студентов из системы EDX в ejudge. Управлющие данные поступают из тега <grader_payload> в виде словаря.

Перед началом:
=========
- Должен быть установлен ejudge >= 3.6.0 (https://ejudge.ru/)
- В Ejudge используется альтернативная раскладка файлов (https://goo.gl/JSEOYe)
- Создать файл login в корне проекта. Первая строка - имя пользователя, вторая - пароль
- Отредактировать файл settings.py. Ввести ip lms, логин и пароль для доступа

Установка
===========
``` git clone https://github.com/madker4/edx-ejudge-grader.git```

Установка зависимостей:
```pip install -r ./requirements.txt ```

Запуск:
=========

``` 
python edx-ejudge-grader.py
```
