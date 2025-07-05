import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re
import json
import os
from dotenv import load_dotenv

# Load config
env_path = ".env"
if os.path.exists(env_path):
    load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

WHITELIST = config.get("whitelist", [])
AUTHORIZED_EMAILS = config.get("authorized_emails", {})
PAID_USERS = config.get("paid_users", [])

# FSM States
class AuthStates(StatesGroup):
    waiting_for_email = State()

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Keyboards
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Авторизация"), KeyboardButton("Помощь оператора"))
    return kb

def auth_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Оплата"), KeyboardButton("Статус подписки"), KeyboardButton("Помощь оператора"))
    return kb

def paid_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Мой доступ"), KeyboardButton("Поддержка"))
    return kb

# Handlers
@dp.message(lambda msg: msg.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    if WHITELIST and str(message.from_user.id) not in WHITELIST:
        return await message.answer("Доступ ограничен.")
    await state.clear()
    await message.answer(
        "Добро пожаловать!\nВоспользуйтесь кнопками ниже.",
        reply_markup=main_keyboard()
    )

@dp.message(lambda msg: msg.text == "Авторизация")
async def start_auth(message: types.Message, state: FSMContext):
    await message.answer("Введите вашу зарегистрированную почту:")
    await state.set_state(AuthStates.waiting_for_email)

@dp.message(AuthStates.waiting_for_email)
async def handle_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+", email):
        return await message.answer("Некорректный формат почты. Попробуйте снова.")

    if email in AUTHORIZED_EMAILS:
        await state.update_data(email=email)
        user_id = str(message.from_user.id)
        is_paid = user_id in PAID_USERS
        kb = paid_keyboard() if is_paid else auth_keyboard()
        await message.answer("Авторизация успешна.", reply_markup=kb)
        await state.clear()
    else:
        await message.answer("Почта не найдена. Попробуйте снова или обратитесь в поддержку.")

@dp.message(lambda msg: msg.text == "Оплата")
async def handle_payment(message: types.Message):
    await message.answer("Для оплаты перейдите по ссылке: https://your-site.com/pay")

@dp.message(lambda msg: msg.text == "Статус подписки")
async def handle_status(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id in PAID_USERS:
        await message.answer("Ваша подписка активна до 01.01.2030")
    else:
        await message.answer("У вас нет активной подписки.")

@dp.message(lambda msg: msg.text in ["Помощь оператора", "Поддержка"])
async def help_operator(message: types.Message):
    admin_id = config.get("admin_id")
    if admin_id:
        await bot.send_message(admin_id, f"Пользователь @{message.from_user.username} ({message.from_user.id}) просит поддержки.")
    await message.answer("Специалист свяжется с вами в ближайшее время.")

@dp.message(lambda msg: msg.text == "Мой доступ")
async def my_access(message: types.Message):
    await message.answer("Ваш доступ к закрытым функциям открыт. Используйте доступные команды.")

# Run bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
