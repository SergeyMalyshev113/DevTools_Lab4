from aiogram import Bot, Dispatcher, types, executor
import json
import os
import time
from dotenv import load_dotenv, find_dotenv
import sqlite3
import keyboard as kb
from random import randint
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from asyncio import Lock



# ------- Глобал переменные -------
load_dotenv(find_dotenv())
bot = Bot(os.getenv('token'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ---------- Data Base ----------
def data_base():
    global db, cursor, dbLock
    db = sqlite3.connect(os.getenv('db'))
    cursor = db.cursor()
    dbLock = Lock()

    table = """
    CREATE TABLE IF NOT EXISTS users (
    	id INT,
    	random_min INT
    )
    """
    cursor.executescript(table)
data_base()

# ----------- Клавиатурa -----------
markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(kb.mem).add(kb.monetka).add(kb.random)
markup_random = types.ReplyKeyboardMarkup(resize_keyboard=True).add(kb.back)

# ---------- Машина состояний ----------
class Form(StatesGroup): # Инициализация состояний для перехода между хэндлерами
    menu = State()
    random_min = State()
    random_max = State()

# -------- Основная функция --------
@dp.message_handler(commands=['start'])
async def start(message):
    userid = message.from_user.id
    async with dbLock:
        cursor.execute("SELECT id FROM users WHERE id = ?", [userid])
        res = cursor.fetchone()
        if res is None:
            cursor.execute("INSERT INTO users(id) VALUES(?)", [userid])
            db.commit()
    await Form.menu.set()
    await message.answer('Привет, я бот для четвёртой лабы по ПО (лох короче какой-то)', reply_markup=markup)


@dp.message_handler(state=Form.menu, text='Вкинь мем')
async def mem(message: types.Message, state: FSMContext):
    userid = message.from_user.id
    key = str(randint(1, 11))
    f = open('mem.json', 'r', encoding='utf-8')
    js = json.loads(f.read())
    await message.answer(js['MemesForBot'][f'{key}'])
    f.close()



@dp.message_handler(state=Form.menu, text='Подбрось монетку')
async def monetka(message: types.Message, state: FSMContext):
    userid = message.from_user.id
    res = randint(1, 2)
    await message.answer('Монетка взлетает ввысь...')
    time.sleep(1.4)
    if res == 1:
        await message.answer('Выпала решка')
    elif res == 2:
        await message.answer('Выпал орёл')


@dp.message_handler(state=Form.menu, text='Рандомное число')
async def random_init(message: types.Message, state: FSMContext):
    userid = message.from_user.id
    await message.answer('Введите минимальное значение:')
    await Form.random_min.set()



@dp.message_handler(state=Form.random_min)
async def random_min(message: types.Message, state: FSMContext):
    try:
        userid = message.from_user.id
        min_val = int(message.text)
        async with dbLock:
            cursor.execute("UPDATE users SET random_min = ? WHERE id = ?", [min_val, userid])
            db.commit()
        await message.answer('Введите максимальное значение:')
        await Form.random_max.set()
    except:
        await message.answer('ты придурка за меня не держи, цифру введи')
        return

@dp.message_handler(state=Form.random_max)
async def random_result(message: types.Message, state: FSMContext):
    try:
        userid = message.from_user.id
        max_val = int(message.text)
        min_val = cursor.execute("SELECT random_min FROM users WHERE id = ?", [userid]).fetchone()[0]
        res = int(randint(min_val, max_val))
        await message.answer(f'Ваше число: {res}')
        await Form.menu.set()
    except:
        await message.answer('ты придурка за меня не держи, цифру введи')
        return



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
