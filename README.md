
# Размещение бота на сервере

Инструкция по размещению бота у себя на сервере
Зайдите в файл .env и замените.

    1.TOKEN- На токен вашего бота.

        BOT_URL- На урл вашего сайта или хостинга обязательно https.

        ADMIN- ID-Телеграм id вашего админа или вашег.

        SHOPID- Создайте свой магазин в tegro money и получите ваш SHOPID.

        SECRETKEY- Получите ваш секретный ключ на tegro money.

        BOT_NICKNAME- подставьте имя вашего бота.

        KEYSMOSERVICE- ваш api ключ на SmoService.

        KEYSMMPANEL- ваш api ключ на SmmPanel.

        USERIDSMOSERVICE- ваше userid на SmoService(написан над api ключом).


Подключитесь к вашему серверу по SSH и FTTP, это делается с помощью программ PuTTy и FileZilla соответсвенно.

Далее необходимо получить HTTPS сертификат, для этого проделайте эту инстркукцию(введите данные софта которые стоит у вас на сервере)
https://certbot.eff.org/

После получение сертификата сохраните два пути к файлам выданные программой в консоли.

Введите эти команды в консоль по очереди

1.

    sudo apt-get install -y nginx
    cd /etc/nginx/sites-available/
    sudo nano telegram_bot.conf

В появившемся поле вписываем это

2.

    server {
            listen 80;
            listen 443 ssl;
            server_name bot.khashtamov.com;
            ssl_certificate Путь Который вы Сохранили;
            ssl_certificate_key Второй Путь Который Вы Сохранили;
            location / {
                proxy_set_header Host $http_host;    
                proxy_redirect off;    
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;    
                proxy_set_header X-Real-IP $remote_addr;    
                proxy_set_header X-Scheme $scheme;    
                proxy_pass http://localhost:8001/;    
        }
    }


Далее прописываем эти три команды

3.

    cd /etc/nginx/sites-enabled/
    sudo ln -s ../sites-available/telegram_bot.conf telegram_bot.conf
    sudo service nginx restart


Дальше надо написать сервис который всегда будет держать наш бот запущеным

4.

    cd etc/systemd/system/
    vim tgbot.service


Дальше в открывшемся редакторе вставьте это

5.

    [Service]
    WorkingDirectory= путь до вашего main файла бота
    User=имя пользоватлья от чего лица нужна запускать в консоле
    ExecStart=/usr/bin/python3 main.py

    [Install]
    WantedBy=multi-user.target
    EOF