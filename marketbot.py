import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, BotCommand, MenuButtonCommands

TOKEN = "8023988031:AAHgSs1mmklF0434Vtr7ZXYKrIG0KT_DIv4"
ADMIN_IDS = [1238294568]  # Replace with actual admin IDs

bot = Bot(token=TOKEN)
dp = Dispatcher()

FILES_DIR = "uploaded_files"
os.makedirs(FILES_DIR, exist_ok=True)  # Ensure the directory exists

CATEGORIES = {
    "SMTP": ["Amazon SES", "SendGrid", "Mailgun", "Postmark", "Elastic Email"],
    "Redirects": ["Open Redirects", "Google Redirect"],
    "Leads": ["Gmail", "AOL", "Office", "Comcast", "Yahoo", "Web.de", "GMX.de"],
    "Hosts": ["Cracked Cpanels", "Created Cpanels"],
    "Logs": ["Office Remax logs", "Bank logs"]
}

STATES_LEADS = ["Gmail", "AOL", "Office", "Comcast", "Yahoo"]
STATES = ["NY", "ID", "OH", "CA", "HI"]

# Function to create the main menu keyboard
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Products", callback_data="menu_products")],
        [InlineKeyboardButton(text="💰 Add Balance", callback_data="menu_balance")],
        [InlineKeyboardButton(text="🛍️ My Purchases", callback_data="menu_purchases")],
        [InlineKeyboardButton(text="📞 Support", callback_data="menu_support")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="menu_profile")]
    ])

def get_category_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat, callback_data=f'cat_{cat}')] for cat in CATEGORIES
    ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]])

def get_subcategory_keyboard(category):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=sub, callback_data=f'sub_{category}_{sub}')] for sub in CATEGORIES[category]
    ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data="back_menu")]])

def get_file_keyboard(category, subcategory, files):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=file, callback_data=f'download_{category}_{subcategory}_{file}')] for file in files
    ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data=f'back_sub_{category}')]])

# Start command handler
@dp.message(Command("start"))
async def start_command(message: Message):
    await bot.set_my_commands([
        BotCommand(command="start", description="Restart the bot"),
        BotCommand(command="menu", description="Show main menu")
    ])
    await bot.set_chat_menu_button(chat_id=message.chat.id, menu_button=MenuButtonCommands())
    await message.reply("Welcome! Select an option:", reply_markup=get_main_menu())

# Handle menu navigation
@dp.callback_query(lambda c: c.data.startswith("menu_"))
async def handle_menu(callback_query: CallbackQuery):
    action = callback_query.data.split("_")[1]
    if action == "products":
        await callback_query.message.edit_text("Select a category:", reply_markup=get_category_keyboard())
    elif action == "balance":
        await callback_query.message.edit_text("To add balance, follow the payment instructions.", reply_markup=get_main_menu())
    elif action == "purchases":
        await callback_query.message.edit_text("Here are your purchased products.", reply_markup=get_main_menu())
    elif action == "support":
        await callback_query.message.edit_text("For support, contact admin: @habnoddigitalshares", reply_markup=get_main_menu())
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('cat_'))
async def list_subcategories(callback_query: CallbackQuery):
    category = callback_query.data.split('_')[1]
    await callback_query.message.edit_text(f"Select a subcategory in {category}:", reply_markup=get_subcategory_keyboard(category))
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('sub_'))
async def list_files(callback_query: CallbackQuery):
    _, category, subcategory = callback_query.data.split('_')
    subcategory_path = os.path.join(FILES_DIR, category, subcategory)

    os.makedirs(subcategory_path, exist_ok=True)  # Ensure directory exists
    files = os.listdir(subcategory_path)
    files_text = "\n".join(files) if files else "No files available."
    
    await callback_query.message.edit_text(
        f"Available files in {subcategory}:\n{files_text}",
        reply_markup=get_file_keyboard(category, subcategory, files)
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('download_'))
async def download_file(callback_query: CallbackQuery):
    _, category, subcategory, filename = callback_query.data.split('_')
    file_path = os.path.join(FILES_DIR, category, subcategory, filename)

    if os.path.exists(file_path):
        await bot.send_document(callback_query.message.chat.id, types.FSInputFile(file_path))
    else:
        await callback_query.message.reply("File not found.")
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('back_'))
async def back_button(callback_query: CallbackQuery):
    action = callback_query.data.split('_')[1]
    if action == "main":
        await callback_query.message.edit_text("Welcome! Select an option:", reply_markup=get_main_menu())
    elif action == "menu":
        await callback_query.message.edit_text("Select a category:", reply_markup=get_category_keyboard())
    elif action.startswith("sub"):
        category = action.split("_")[1]
        await callback_query.message.edit_text(f"Select a subcategory in {category}:", reply_markup=get_subcategory_keyboard(category))
    await callback_query.answer()

# File upload handler (Admins Only)
@dp.message(lambda message: message.document)
async def upload_file(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("❌ You are not authorized to upload files.")
        return
    
    # Ensure caption is provided
    if not message.caption:
        await message.reply("⚠️ Please provide a category in the caption (e.g., 'SMTP', 'Leads').")
        return

    category = message.caption.strip()
    found_category = None

    # Validate category
    for cat in CATEGORIES:
        if category.lower() == cat.lower():
            found_category = cat
            break

    if not found_category:
        await message.reply(f"❌ Invalid category. Use one of: {', '.join(CATEGORIES.keys())}")
        return

    # Define storage path
    category_path = os.path.join(FILES_DIR, found_category)
    os.makedirs(category_path, exist_ok=True)

    file_path = os.path.join(category_path, message.document.file_name)
    await message.document.download(destination_file=file_path)
    
    await message.reply(f"✅ File '{message.document.file_name}' uploaded to {found_category} successfully!")

# Setup bot commands
async def setup_bot_menu():
    await bot.set_my_commands([
        BotCommand(command="start", description="Restart the bot"),
        BotCommand(command="menu", description="Open main menu")
    ])
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

# Start bot
async def main():
    await setup_bot_menu()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
