from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name=__name__)


@router.message(Command("admin"))
async def admin_link(message: Message) -> None:
    await message.answer("Админка: /admin/login (через веб-панель FastAPI)")
