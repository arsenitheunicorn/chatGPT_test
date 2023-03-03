import datetime
import os
import sys
from time import sleep
import telebot
import aifuncs
from myclasses import Filename, UserActive, Conversation

base_prompt_path = "prompt_v4.txt"

models = {
    'ada': 'text-ada-001',
    # 'ada': 'text-embedding-ada-002',
    'davinci': 'text-davinci-003',
    'babbage': 'babbage',
    'curie': 'text-curie-001',
    'chat': 'gpt-3.5-turbo'
}


if len(sys.argv) > 1:
    bot_config_key = sys.argv[1]
else:
    bot_config_key = 'ada'


if bot_config_key in models:
    model = models[bot_config_key]
    token = os.getenv(f"TELEBOT_{bot_config_key.upper()}_API_KEY")
else:
    raise KeyError(f"wrong config: {bot_config_key}")


bot = telebot.TeleBot(
    token=token
)

bot_manager = Conversation()


@bot.message_handler(commands=['voice_off'])
def voice_on(message: telebot.types.Message):
    username = message.from_user.username
    if username not in bot_manager.users:
        bot_manager.new_user(UserActive(username, message.chat.id))
    user: UserActive = bot_manager.users[username]

    user.coachVoice = False
    bot.send_message(
        message.chat.id,
        'I will give answers in **text** mode'
    )


@bot.message_handler(commands=['start'])
def start_conversation(message: telebot.types.Message):
    username = message.from_user.username
    chat_id = message.chat.id
    if username not in bot_manager.users:
        bot_manager.new_user(
            UserActive(
                username=username,
                chat_id=chat_id
            )
        )
    if not bot_manager.users[username].isActive:
        if bot_manager.users[username].prompt_text is not None:
            prompt = bot_manager.users[username].prompt_text
        else:
            with open(base_prompt_path, 'r') as f:
                prompt = f.read()
        bot_manager.activate_user(username)
        filename = Filename(
                    username, bot_manager.users[username].conv_id, bot_config_key
                ).prompt_log
        if bot_config_key == 'chat':
            aifuncs.write_logs_json(
                filename,
                role='system',
                content=prompt.strip()
            )
        else:
            aifuncs.write_logs(
                filename,
                prompt + "\n"
            )
        bot.send_message(
            chat_id=chat_id,
            text="What's on your mind today that you would like to work on in our coaching session?"
        )


@bot.message_handler(commands=['exit'])
def exit_conversation(message: telebot.types.Message):
    username = message.from_user.username
    user: UserActive = bot_manager.users[username]
    if user.isActive:
        # inform user that a summary will come
        bot.send_message(
            user.chat_id,
            "You have ended the conversation!\nYour summary will arrive in a blink..."
        )
        filename = Filename(
            username, user.conv_id, bot_config_key
        ).prompt_log
        if bot_config_key == 'chat':
            summary = aifuncs.call_chatgpt(
                prompt_path=filename,
                is_summary=True
            )
        else:
            summary = aifuncs.call_openapi(
                prompt_path=filename,
                model_engine=model,
                is_summary=True
            )
        bot.send_message(
            user.chat_id,
            text=summary
        )

        bot_manager.deactivate_user(username)


@bot.message_handler(commands=['prompt'])
def set_prompt(message: telebot.types.Message):
    username = message.from_user.username
    chat_id = message.chat.id
    if username not in bot_manager.users:
        bot_manager.new_user(
            UserActive(
                username=username,
                chat_id=chat_id
            )
        )
    user: UserActive = bot_manager.users[username]
    bot.send_message(
        chat_id=chat_id,
        text="Send me your prompt!"
    )
    bot.register_next_step_handler(
        message=message,
        callback=save_prompt
    )


def save_prompt(message: telebot.types.Message):
    new_prompt: str = message.text
    username: str = message.from_user.username
    bot_manager.users[username].prompt_text = new_prompt
    bot.send_message(
        message.chat.id,
        "Prompt saved! How about we /start a conversation?"
    )


@bot.message_handler(content_types=['text', 'voice'])
def answer_coach(message: telebot.types.Message):
    username = message.from_user.username
    user: UserActive = bot_manager.users.get(username)
    if message.text.startswith('/'):
        return None
    if user.isActive:
        filename_obj = Filename(username, user.conv_id, bot_config_key)
        prompt_path: str = filename_obj.prompt_log
        if message.content_type == 'text':
            text = message.text
        else:
            voice_path = filename_obj.voice_path
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(voice_path, 'wb') as f:
                f.write(downloaded_file)
            text = aifuncs.voice2text(voice_path)
            bot.reply_to(
                message,
                text="<i>"+text+"</i>",
                parse_mode='HTML'
            )
        text.replace('\n', ' ')
        if bot_config_key != 'chat':
            aifuncs.write_logs(
                prompt_path,
                "Client: " + text + "\nCoach: "
            )
            answer = aifuncs.call_openapi(prompt_path, model).replace('\n', ' ')
            aifuncs.write_logs(
                prompt_path,
                answer + "\n"
            )
        else:
            aifuncs.write_logs_json(
                prompt_path,
                role='user',
                content=text.strip()
            )
            answer = aifuncs.call_chatgpt(prompt_path)
            aifuncs.write_logs_json(
                prompt_path,
                role='assistant',
                content=answer.strip()
            )

        if user.coachVoice:
            coach_voice_path: str = f'voicing/{bot_config_key}/{username}_' + datetime.datetime.now(
            ).strftime('%y%m%d-%H%M%S') + ".mpeg"
            result = aifuncs.voice_generate(
                text=answer.strip(),
                filename=coach_voice_path
            )
            if result:
                with open(coach_voice_path, 'rb') as f:
                    bot.send_voice(
                        user.chat_id,
                        voice=f
                    )
            else:
                print('failed w/ voice')
                bot.send_message(
                    user.chat_id,
                    text=answer
                )
        else:
            bot.send_message(
                user.chat_id,
                text=answer
            )


@bot.message_handler(commands=['voice_on'])
def voice_on(message: telebot.types.Message):
    username = message.from_user.username
    user: UserActive = bot_manager.users[username]
    user.coachVoice = True
    bot.send_message(
        message.chat.id,
        'I will give answers in **voice** mode'
    )


while True:
    try:
        bot.infinity_polling()
    except Exception:
        sleep(10)
