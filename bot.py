from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("token"))
dp = Dispatcher()

def setup_database():
    with sqlite3.connect("orders.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category TEXT NOT NULL,
                            username TEXT NOT NULL,
                            address TEXT NOT NULL,
                            description TEXT,
                            status TEXT DEFAULT 'Заказ принят'
                        )''')

setup_database()

def create_category_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Еда", callback_data="category:Еда")],
        [InlineKeyboardButton(text="Запчасти", callback_data="category:Запчасти")],
        [InlineKeyboardButton(text="Мебель", callback_data="category:Мебель")],
    ])

user_data = {}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Добро пожаловать в LooT Бот! Выберите категорию заказа:",
        reply_markup=create_category_keyboard()
    )

@dp.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery):
    if callback_query.data.startswith("category:"):
        category = callback_query.data.split(":")[1]
        user_data[callback_query.from_user.id] = {"category": category}
        await bot.send_message(callback_query.from_user.id, "Введите ваше имя:")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_data:
        if "username" not in user_data[user_id]:
            user_data[user_id]["username"] = message.text
            await message.answer("Введите адрес доставки:")
        elif "address" not in user_data[user_id]:
            user_data[user_id]["address"] = message.text
            await message.answer("Введите описание заказа:")
        elif "description" not in user_data[user_id]:
            user_data[user_id]["description"] = message.text
            data = user_data.pop(user_id)

            with sqlite3.connect("orders.db") as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO orders (category, username, address, description)
                                  VALUES (?, ?, ?, ?)''',
                               (data["category"], data["username"], data["address"], data["description"]))
                order_id = cursor.lastrowid

            await message.answer(f"Ваш заказ оформлен! Номер вашего заказа: {order_id}")
    elif message.text.isdigit():
        order_id = int(message.text)
        with sqlite3.connect("orders.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
            result = cursor.fetchone()

        if result:
            await message.answer(f"Статус вашего заказа: {result[0]}")
        else:
            await message.answer("Заказ с таким номером не найден.")
    elif message.text == "/status":
        await message.answer("Введите номер заказа для проверки статуса:")

async def main():
    print("Ваш личный бот LooT Запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
