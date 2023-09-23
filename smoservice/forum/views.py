import aiohttp_jinja2
from core.handlers import Balance

# создаем функцию, которая будет отдавать html-файл
@aiohttp_jinja2.template("index.html")
async def index(request):
    await Balance.tegro_success(request)
    return {'title': 'Пишем первое приложение на aiohttp'}
