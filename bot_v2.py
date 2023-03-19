import datetime
import os
import sys
from time import sleep
import telebot
import aifuncs
from myclasses import Filename, UserActive, Conversation
import pretreatment

base_prompt_path = "prompts/prompt_main.txt"

models = {
    'ada': 'text-ada-001',
    # 'ada': 'text-embedding-ada-002',
    'davinci': 'text-davinci-003',
    'babbage': 'babbage',
    'curie': 'text-curie-001',
    'chat': 'gpt-3.5-turbo',
    'script': 'gpt-3.5-turbo'
}


if len(sys.argv) > 1:
    bot_config_key = sys.argv[1]
else:
    bot_config_key = 'script'


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
                chat_id=chat_id,
                coachVoice=True
            )
        )
    if not bot_manager.users[username].isActive:
        bot_manager.activate_user(username)

        bot.send_message(
            chat_id=chat_id,
            text=pretreatment.step_call(user_active=bot_manager.users[username])
        )
        # bot_manager.users[username].pretreatment_step += 1


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
        # input processing
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

        # scripting
        if user.pretreatment_step is not None:
            if user.pretreatment_step == 0:
                name = pretreatment.extract_info('Name', text)
                setattr(user.user_data, 'name', name)
            elif user.pretreatment_step == 1:
                goal = pretreatment.extract_info('Goal', text)
                setattr(user.user_data, 'goal', goal)
            elif user.pretreatment_step in [2, 5, 7]:
                if not pretreatment.yes_or_no(text):
                    user.pretreatment_step -= .5
            elif user.pretreatment_step == 3:
                setattr(user.user_data, 'attempts', text)
            elif user.pretreatment_step == 4:
                setattr(user.user_data, 'stopping', text)
            elif user.pretreatment_step == 2.5 or user.pretreatment_step == 5.5:
                user.pretreatment_step -= 1.5

            # increment step after conditional checking
            user.pretreatment_step += True
            if user.pretreatment_step < 8:
                ### Need to add SMART module here
                # if user.pretreatment_step != 6:
                #     answer = pretreatment.step_call(user)
                # else:
                #     pass
                answer = pretreatment.step_call(user)
            else:
                prompt = pretreatment.read_prompt(base_prompt_path, user, 'main')

                filename = Filename(
                    username, bot_manager.users[username].conv_id, bot_config_key
                ).prompt_log
                aifuncs.write_logs_json(
                        filename,
                        role='system',
                        content=prompt.strip()
                )
                # replace later
                answer = "So, let us start our discussion!"
                user.pretreatment_step = None

        # live dialogue
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

        # sending answer
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
