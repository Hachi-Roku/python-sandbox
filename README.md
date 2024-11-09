# python-sandbox
Python sandbox projects.

# ТРЕБОВАНИЯ К СОДЕРЖАНИЮ И ОФОРМЛЕНИЮ ОТЧЕТА

Результатом выполнения каждой лабораторной работы является отчёт,
сохраненный в файле с расширением pdf. Отчет должен содержать задание,
скриншоты примеров работы веб-приложения, примеры выполнения задания,
код приложения с комментариями, примеры выполняемых команд и использу-
емых скриптов для деплоя на PaaS-системы, содержимое файлов переменных
окружения и т. д., структуру каталогов и файлов веб-проекта.
Преподавателю также отправляется рецензия на предыдущий вариант ра-
боты, если она сдается повторно после исправления замечаний.

Каждое приложение должно обеспечивать
проверку на робота с помощью капчи или любой другой технологии. Размести-
те объекты отображения и ввода удобно для пользователя.

# Вариант 20

Веб-приложение должно формировать новое изображение на основе ис-
ходного путем сдвига по замкнутым прямоугольным составляющим на опреде-
ленное число пикселов, которое задает пользователь. Например, сдвигается
внешняя рамка, затем вторая и так до внутренней части. Учесть, что размер
сдвига внутренней части зависит от размера внутренней части и не должен пре-
вышать максимального циклического сдвига по условному кругу. Нарисовать
график распределения цветов для исходного изображения.

# Environemnt
1. For google recaptcha v2 we need to setup 2 key-value pairs
1.1. For local start add .env file, containing RECAPTCHA_SECRET_KEY, RECAPTCHA_PUBLIC_KEY values (using google recaptcha v2)
1.2. For renderer.com start add same values from 1.1. Environment Variables

# Activate virtual environment
`pipenv shell`

# Exit virtual environment
`exit`

# Run project

2. Run `pipenv run uvicorn src.main:app --reload OR ./start.sh`

# Run test
`pytest`

# Using app
Go to /upload-image
Fill in the form
Click "submit" button
See results, click link below to upload one more or navigate yourselves
