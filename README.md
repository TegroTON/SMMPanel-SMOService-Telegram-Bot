<br/>
<p align="center">
  <a href="https://github.com/m1ja/SMMTestBot">
    <img src="static/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Smoservice Bot</h3>

  <p align="center">
    Система автоматизированной раскрутки и продвижения в социальных сетях❗️
    <br/>
    <br/>
    <a href="https://github.com/m1ja/SMMTestBot"><strong>Explore the docs »</strong></a>
    <br/>
    <br/>
    <a href="https://github.com/m1ja/SMMTestBot">View Demo</a>
    .
    <a href="https://github.com/m1ja/SMMTestBot/issues">Report Bug</a>
    .
    <a href="https://github.com/m1ja/SMMTestBot/issues">Request Feature</a>
  </p>
</p>

![Downloads](https://img.shields.io/github/downloads/m1ja/SMMTestBot/total) ![Contributors](https://img.shields.io/github/contributors/m1ja/SMMTestBot?color=dark-green) ![Issues](https://img.shields.io/github/issues/m1ja/SMMTestBot) ![License](https://img.shields.io/github/license/m1ja/SMMTestBot) 

## Table Of Contents

* [About the Project](#about-the-project)
* [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Authors](#authors)
* [Acknowledgements](#acknowledgements)

## About The Project

![Screen Shot](static/main_menu.png)

🚀 SmmTegroTest_Bot - Ваш идеальный инструмент для продвижения в социальных сетях! Получайте больше подписчиков, просмотров и многого другого с легкостью и эффективностью.

Основные функции:
🔹 Новый заказ: Быстро и удобно создайте заказ на накрутку нужного параметра.
🔹 История: Отслеживайте все свои заказы и их статус в одном месте.
🔹 Кошелек: Управляйте своими средствами, пополняйте баланс и оплачивайте услуги.
🔹 Рефералы: Приглашайте друзей и знакомых, получая вознаграждение за их активность.
🔹 Чеки: Поделитесь деньгами с кем-либо, используя простую ссылку для передачи.
🔹 Мои боты: Уникальный функционал! Создайте копию этого бота с новым ID.

Присоединяйтесь к нам и делайте ваш аккаунт популярным!

## Built With

Бот разработан с использованием современных технологических решений, обеспечивающих высокую производительность и стабильность работы. Использование асинхронных библиотек позволяет боту быстро и эффективно обрабатывать большое количество запросов, адаптируясь к высоким требованиям современных пользователей.


* [python 3](https://www.python.org/downloads/)
* [aiohttp](https://docs.aiohttp.org/en/v3.8.1/web_advanced.html)
* [aiogram](https://aiogram.dev/)
* [sqlite](https://www.sqlite.org/index.html)

## Getting Started

Для успешной настройки и стабильной работы бота необходимо следовать нижеуказанным техническим требованиям:

* Сервер:
Хостинг: Рекомендуется использовать VPS или выделенный сервер для оптимальной производительности и надежности. Сервер должен иметь стабильное интернет-соединение и соответствующие ресурсы (CPU, RAM) в зависимости от ожидаемой нагрузки.
Операционная система:
Рекомендуются современные дистрибутивы Linux, такие как Ubuntu, CentOS или Debian. Однако большинство UNIX-подобных систем также подойдут.
Программное обеспечение:
Python 3: Убедитесь, что на сервере установлена последняя стабильная версия Python 3. Это основной язык программирования, на котором написан ваш бот.

* pip: Система управления пакетами для Python. Необходима для установки необходимых библиотек и зависимостей для вашего бота.

* Примечание:
Перед началом настройки рекомендуется проверить все установленное программное обеспечение на актуальность версий и наличие всех необходимых зависимостей.

### Prerequisites

Для корректной установки и функционирования бота убедитесь, что следующие библиотеки и их версии установлены на вашем сервере:
```sh
aiofiles==23.1.0
aiogram==3.0.0rc2
aiohttp==3.8.5
aiohttp-jinja2==1.5.1
aiosignal==1.3.1
annotated-types==0.5.0
anyio==3.7.1
asgiref==3.7.2
async-timeout==4.0.2
attrs==23.1.0
beautifulsoup4==4.12.2
blinker==1.6.2
callback==0.0.1
certifi==2023.7.22
charset-normalizer==3.2.0
click==8.1.7
colorama==0.4.6
Django==4.2.5
fastapi==0.103.1
Flask==2.3.3
frozenlist==1.4.0
idna==3.4
itsdangerous==2.1.2
Jinja2==3.1.2
lxml==4.9.3
magic-filter==1.0.11
Markdown==3.4.4
MarkupSafe==2.1.3
multidict==6.0.4
pydantic==2.2.1
pydantic_core==2.6.1
python-dotenv==1.0.0
requests==2.31.0
sniffio==1.3.0
soupsieve==2.4.1
sqlparse==0.4.4
starlette==0.27.0
typing_extensions==4.7.1
tzdata==2023.3
urllib3==2.0.4
validators==0.21.2
Werkzeug==2.3.7
yarl==1.9.2
```
Для автоматической установки всех необходимых библиотек, вы можете использовать файл req.txt с приведенным выше содержимым, выполнив команду:
```sh
pip install -r req.txt
```
Это обеспечит установку всех нужных зависимостей для надежной работы вашего бота.

### Installation

* 1. Настройка файла .env для вашего бота
Для корректной работы вашего бота необходимо правильно настроить файл конфигурации .env. Пройдите по следующим подшагам:
    * 1.1. Откройте файл .env в редакторе кода.

    * 1.2. Настройка API token бота в Telegram:
Получите api token вашего бота в Telegram.
Вставьте его рядом с графой apitoken.
    * 1.3. Настройка данных магазина в Tegro Money:
Получите shopid и secret key вашего магазина в Tegro Money.
Укажите их в соответствующих графах файла.
    * 1.4. Указание администратора бота:
Укажите user id пользователя Telegram, который будет администратором вашего бота.
    * 1.5. Указание имени бота:
    * 1.6. Настройка данных для SMOService:
Укажите ваш api key в графе для SMOService.
Укажите ваш user id в соответствующей графе для SMOService.
    * 1.7. Настройка данных для SMMPanel:
Укажите ваш api key в графе для SMMPanel.
Укажите ваш user id в соответствующей графе для SMMPanel.
    * 1.9. Сохраните и закройте файл .env.
* 2.

## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

## Roadmap

See the [open issues](https://github.com/m1ja/SMMTestBot/issues) for a list of proposed features (and known issues).

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.
* If you have suggestions for adding or removing projects, feel free to [open an issue](https://github.com/m1ja/SMMTestBot/issues/new) to discuss it, or directly create a pull request after you edit the *README.md* file with necessary changes.
* Please make sure you check your spelling and grammar.
* Create individual PR for each suggestion.
* Please also read through the [Code Of Conduct](https://github.com/m1ja/SMMTestBot/blob/main/CODE_OF_CONDUCT.md) before posting your first idea as well.

### Creating A Pull Request

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See [LICENSE](https://github.com/m1ja/SMMTestBot/blob/main/LICENSE.md) for more information.

## Authors

* **Shaan Khan** - *Comp Sci Student* - [Shaan Khan](https://github.com/ShaanCoding/) - *Built ReadME Template*

## Acknowledgements

* [ShaanCoding](https://github.com/ShaanCoding/)
* [Othneil Drew](https://github.com/othneildrew/Best-README-Template)
* [ImgShields](https://shields.io/)
