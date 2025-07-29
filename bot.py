import asyncio
import logging
import os
import random
import sys
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.markdown import hbold
from asgiref.sync import sync_to_async

from transactions.utils import send_sms

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django

django.setup()

from accounts.models import CustomUser
from notification.models import Notification

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8114840874:AAGr-myWUesy1GeoNcal2ltdyDjbNoKva9o"  # Move to environment variables

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Constants
MAX_VERIFICATION_ATTEMPTS = 3
VERIFICATION_CODE_LENGTH = 6


class VerificationStates(StatesGroup):
    WAITING_FOR_CODE = State()


def generate_verification_code() -> str:
    """Generate verification code with specified length"""
    return str(random.randint(
        10 ** (VERIFICATION_CODE_LENGTH - 1),
        (10 ** VERIFICATION_CODE_LENGTH) - 1
    ))


def mask_phone_number(phone_number: str) -> str:
    """Mask phone number for privacy"""
    if not phone_number or len(phone_number) < 5:
        return "*****"
    return f"{phone_number[:3]}****{phone_number[-2:]}"


async def create_notification(user: CustomUser, message: str) -> None:
    """Create notification for user"""
    await sync_to_async(Notification.objects.create)(
        user=user,
        message=message,
        notification_type="telegram_verification",
    )


async def get_user_by_uuid(uuid: str) -> Optional[CustomUser]:
    """Get user by telegram link token"""
    try:
        return await sync_to_async(CustomUser.objects.get)(telegram_link_token=uuid)
    except CustomUser.DoesNotExist:
        logger.warning(f"User not found with UUID: {uuid}")
        return None
    except Exception as e:
        logger.error(f"Error getting user by UUID: {e}", exc_info=True)
        return None


async def update_user_telegram_data(
        user: CustomUser,
        telegram_id: int,
        username: str
) -> bool:
    """Update user's telegram data"""
    try:
        user.telegram_id = telegram_id
        user.telegram_username = username or "Noma'lum"
        await sync_to_async(user.save)()
        return True
    except Exception as e:
        logger.error(f"Error updating user telegram data: {e}", exc_info=True)
        return False


async def send_verification_code(phone_number: str, code: str) -> bool:
    """Send verification code to user's phone"""
    try:
        send_sms(phone_number, f"Telegram akkauntingizni bog'lash uchun tasdiqlash kodi: {code}")
        logger.info(f"Sending verification code {code} to {mask_phone_number(phone_number)}")
        return True
    except Exception as e:
        logger.error(f"Error sending verification code: {e}", exc_info=True)
        return False


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Handle /start command with UUID"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "👋 Salom! Botdan foydalanish uchun quyidagilarni bajaring:\n\n"
            "1. Web saytimizda ro'yxatdan o'ting\n"
            "2. Profilingizdagi 'Telegram bilan ulash' tugmasini bosing\n"
            "3. Sizga yuborilgan havola orqali botga qayta kiring"
        )
        return

    uuid = args[1].strip()
    telegram_id = message.from_user.id
    username = message.from_user.username or "Noma'lum"

    user = await get_user_by_uuid(uuid)
    if not user:
        await message.answer("❌ Noto'g'ri havola yoki u eskirgan.")
        return

    if user.telegram_id:
        if user.telegram_id == telegram_id:
            await message.answer("ℹ️ Akkauntingiz allaqachon bog'langan.")
        else:
            await message.answer("❌ Bu havola boshqa Telegram hisobiga tegishli.")
        return

    code = generate_verification_code()
    await state.update_data(
        user_id=user.id,
        verification_code=code,
        attempts_left=MAX_VERIFICATION_ATTEMPTS,
    )

    try:
        if not await send_verification_code(user.phone_number, code):
            raise Exception("SMS jo'natib bo'lmadi")

        masked = mask_phone_number(user.phone_number)
        await message.answer(
            f"📨 Tasdiqlash kodi {masked} raqamiga yuborildi.\n"
            f"Kodni kiriting ({MAX_VERIFICATION_ATTEMPTS} marta urinish):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Kodni qayta yuborish")]],
                resize_keyboard=True,
            ),
        )
        await state.set_state(VerificationStates.WAITING_FOR_CODE)

    except Exception as e:
        logger.error(f"/start xatolik: {e}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()


@router.message(F.text == "Kodni qayta yuborish")
async def handle_resend_code(message: Message, state: FSMContext) -> None:
    """Handle code resend request"""
    data = await state.get_data()
    user_id = data.get("user_id")

    if not user_id:
        await message.answer("❌ Sessiya tugagan. Iltimos, /start ni qayta bosing.")
        await state.clear()
        return

    try:
        user = await sync_to_async(CustomUser.objects.get)(id=user_id)
        code = generate_verification_code()
        await state.update_data(
            verification_code=code,
            attempts_left=MAX_VERIFICATION_ATTEMPTS
        )

        if not await send_verification_code(user.phone_number, code):
            raise Exception("SMS jo'natib bo'lmadi")

        masked = mask_phone_number(user.phone_number)
        await message.answer(f"🔄 Yangi kod {masked} raqamiga yuborildi. Kodni kiriting.")

    except Exception as e:
        logger.error(f"Qayta yuborishda xatolik: {e}", exc_info=True)
        await message.answer(
            "❌ Kod yuborilmadi. Keyinroq urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()


@router.message(VerificationStates.WAITING_FOR_CODE)
async def handle_verification_code(message: Message, state: FSMContext) -> None:
    """Handle verification code input"""
    data = await state.get_data()
    entered_code = message.text.strip()
    correct_code = data.get("verification_code")
    attempts_left = data.get("attempts_left", MAX_VERIFICATION_ATTEMPTS)
    user_id = data.get("user_id")

    if not user_id or not correct_code:
        await message.answer("❌ Sessiya tugagan. /start ni qayta bosing.")
        await state.clear()
        return

    if entered_code == correct_code:
        try:
            user = await sync_to_async(CustomUser.objects.get)(id=user_id)
            success = await update_user_telegram_data(
                user,
                message.from_user.id,
                message.from_user.username,
            )

            if not success:
                raise Exception("User ma'lumotlarini yangilab bo'lmadi")

            await create_notification(
                user,
                f"Telegram akkauntingiz {hbold(user.telegram_username)} bog'landi.",
            )

            await message.answer(
                f"✅ Tabriklaymiz, {hbold(user.first_name or user.username)}!\n"
                "Telegram akkauntingiz muvaffaqiyatli bog'landi.",
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Bog'lashda xatolik: {e}", exc_info=True)
            await message.answer(
                "❌ Tizim xatosi. Keyinroq urinib ko'ring.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
    else:
        attempts_left -= 1
        await state.update_data(attempts_left=attempts_left)

        if attempts_left > 0:
            await message.answer(
                f"❌ Noto'g'ri kod. Qolgan urinishlar: {attempts_left}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="Kodni qayta yuborish")]],
                    resize_keyboard=True,
                ) if attempts_left == 1 else None
            )
        else:
            await message.answer(
                f"🚫 {MAX_VERIFICATION_ATTEMPTS} marta noto'g'ri kod kiritdingiz. "
                "Iltimos, /start ni qayta bosing.",
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.clear()


async def main() -> None:
    """Main function to start the bot"""
    logger.info("🤖 Bot ishga tushmoqda...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Botda kritik xato: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())