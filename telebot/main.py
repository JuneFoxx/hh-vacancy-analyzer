import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from handlers import search

logging.basicConfig(level=logging.INFO)
load_dotenv()

async def main():
    bot = Bot(token=os.environ.get("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(search.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())