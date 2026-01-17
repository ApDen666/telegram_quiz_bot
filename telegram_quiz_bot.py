import aiosqlite
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
import pandas as pd
import csv

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = '8001977125:AAG11htfXg59emudbtQ0QoWzUVuVhEy7qbQ'

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

# Зададим имя базы данных
DB_NAME = 'quiz_bot.db'

# Структура квиза
quiz_data = [
    {#1
        'question': '1. Что такое Python?',
        'options': ['Язык программирования', 'Тип данных', 'Музыкальный инструмент', 'Змея на английском'],
        'correct_option': 0
    },
    {#2
        'question': '2. Какой тип данных используется для хранения целых чисел?',
        'options': ['int', 'float', 'str', 'natural'],
        'correct_option': 0
    },
    {#3
        'question': '3. Какой из следующих типов данных в Python является неизменяемым?',
        'options': ['Список', 'Словарь', 'Кортеж', 'Множество'],
        'correct_option': 2
    },
    {#4
        'question': '4. Какой метод используется для добавления элемента в конец списка в Python?',
        'options': ['insert()', 'append()', 'extend()', 'add()'],
        'correct_option': 1
    },
    {#5
        'question': '5. Какой из следующих операторов используется для проверки равенства в Python?',
        'options': ['=', '==', '!=', '<='],
        'correct_option': 1
    },
    {#6
        'question': '6. Какой из следующих операторов используется для проверки равенства в Python?',
        'options': ['json', 'csv', 'xml', 'os'],
        'correct_option': 1
    },
    {#7
        'question': '7. Какой из следующих методов используется для чтения всех строк из файла в Python?',
        'options': ['read()', 'readline()', 'readlines()', 'readall()'],
        'correct_option': 2
    },
    {#8
        'question': '8. Какой из следующих терминов относится к концепции ООП, позволяющей создавать новый класс на основе существующего?',
        'options': ['Инкапсуляция', 'Полиморфизм', 'Наследование', 'Абстракция'],
        'correct_option': 2
    },
    {#9
        'question': '9. Какой из следующих фреймворков используется для создания веб-приложений на Python?',
        'options': ['NumPy', 'Pandas', 'Matplotlib', 'Flask'],
        'correct_option': 3
    },
    {#10
        'question': '10. Какой из следующих методов используется для получения длины строки в Python?',
        'options': ['length()', 'size()', 'count()', 'len()'],
        'correct_option': 3
    },
]

# Сохранение вопросов и ответов в файл
temp=[['Вопросы','Ответы']]
for i in quiz_data:
    if str(i['question']).replace("'","").split(".")[1][0]==" ":
        temp.append([str(i['question']).replace("'","").split(".")[1][1:],str(i['options'][int(i['correct_option'])])])
    else:
        temp.append([str(i['question']).replace("'","").split(".")[1],str(i['options'][int(i['correct_option'])])])
with open('question-answer.csv', 'w', newline='') as f:
    csv.writer(f).writerows(temp)
#data = pd.read_csv('/content/question-answer.csv')
#print(data.head(10))


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    user_stat = await get_user_stat(callback.from_user.id)

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    user_stat+=1

    await update_quiz_index(callback.from_user.id, current_question_index, user_stat)


    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    user_stat = await get_user_stat(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, user_stat)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))
    builder.add(types.KeyboardButton(text="Продолжить игру"))

    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


async def get_question(message, user_id):
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    # Начинаем квиз
    user_id = message.from_user.id
    current_question_index = 0
    user_stat = 0
    await update_quiz_index(user_id, current_question_index, user_stat)
    await get_question(message, user_id)

async def begining_quiz(message):
    # Продолжаем квиз
    user_id = message.from_user.id
    await get_quiz_index(user_id)
    await get_question(message, user_id)


async def user_stat(message):
    # Подключаемся к базе данных
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT user_stat FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            await message.answer("Ваш результат:\nВерных ответов - "+str(results[0])+" (из "+str(len(quiz_data))+")")
            if results is not None:
                return results[0]
            else:
                return 0


async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def get_user_stat(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT user_stat FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def update_quiz_index(user_id, index, user_stat):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, user_stat) VALUES (?, ?, ?)', (user_id, index, user_stat))
        # Сохраняем изменения
        await db.commit()


# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))

async def cmd_quiz(message: types.Message):
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

@dp.message(F.text=="Статистика")
async def cmd_quiz(message: types.Message):
    #await message.answer(f"Ваш результат:")
    await user_stat(message)

@dp.message(F.text=="Продолжить игру")
async def cmd_quiz(message: types.Message):
    await message.answer(f"Итак, продолжим...")
    await begining_quiz(message)

async def create_table():
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, user_stat INTEGER)''')
        # Сохраняем изменения
        await db.commit()



# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())