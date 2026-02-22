import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
API_TOKEN = "8485665573:AAGCRSfIMwtfcqLYqNin_JkewVtFGhucKjM"
ADMIN_ID = 7287689795

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('anketa.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, tg_id INTEGER, username TEXT, name TEXT, age TEXT, city TEXT)')
conn.commit()

class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! 👋 Как тебя зовут?")
    await state.set_state(Form.name)

# Команда /list
@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT name, username, city FROM users")
    users = cursor.fetchall()
    if not users:
        await message.answer("База данных пока пуста.")
    else:
        text = "📋 Список анкет:\n\n"
        for u in users:
            text += f"👤 {u[0]} ({u[1]}) - {u[2]}\n"
        await message.answer(text)

# Обработка имени
@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Обработка возраста
@dp.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Из какого ты города?")
    await state.set_state(Form.city)

# Финал анкеты
@dp.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    age = data.get('age')
    city = message.text
    tg_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "нет ника"

    cursor.execute("INSERT INTO users (tg_id, username, name, age, city) VALUES (?, ?, ?, ?, ?)",
                   (tg_id, username, name, age, city))
    conn.commit()

    admin_text = f"🔔 Новая анкета!\n👤 {name}, {age} лет\n🏙 {city}\n📎 {username}"
    
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Ошибка уведомления: {e}")

    await message.answer("✅ Данные сохранены! Спасибо.")
    await state.clear()

async def main():
    # Важно: удаляем вебхуки перед запуском, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
