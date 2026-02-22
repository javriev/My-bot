import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = "8485665573:AAHl6NeWUyCmE_3jpTmptA0PJBl1lykoC_I"
ADMIN_ID = 7287689795

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = sqlite3.connect('anketa.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, tg_id INTEGER, username TEXT, name TEXT, age TEXT, city TEXT)')
conn.commit()

class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

@dp.message_handler(commands='start')
async def start(message: types.Message):
    await message.answer("Привет! Как тебя зовут?")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await Form.age.set()

@dp.message_handler(state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Из какого ты города?")
    await Form.city.set()

@dp.message_handler(state=Form.city)
async def process_city(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_info = {
        "tg_id": message.from_user.id,
        "username": f"@{message.from_user.username}" if message.from_user.username else "нет ника",
        "name": data['name'],
        "age": data['age'],
        "city": message.text
    }
    
    cursor.execute("INSERT INTO users (tg_id, username, name, age, city) VALUES (?, ?, ?, ?, ?)",
                   (user_info["tg_id"], user_info["username"], user_info["name"], user_info["age"], user_info["city"]))
    conn.commit()

    # Уведомление тебе в личку
    admin_text = (f"🔔 Новая анкета!\n\n👤 Имя: {user_info['name']}\n🎂 Возраст: {user_info['age']}\n"
                  f"🏙 Город: {user_info['city']}\n📎 Ник: {user_info['username']}")
    await bot.send_message(ADMIN_ID, admin_text)

    await message.answer("✅ Готово! Данные сохранены.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
