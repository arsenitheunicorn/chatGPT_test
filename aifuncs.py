import os
import time
import requests
import openai
import whisper
import json
from typing import Optional, Literal

openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.Model.retrieve("text-davinci-003")
model = whisper.load_model("base.en")


def estimate_tokens(text):
    """
    As per https://openai.com/api/pricing/, prices are per 1,000 tokens. You can think of tokens as pieces of words, where 1,000 tokens is about 750 words. This paragraph is 35 tokens.
    :param text:
    :return:
    """
    return len(text.split()) / 0.75


def write_logs(file_path, data):
    """
    Append data to the prompt log-file
    :param file_path: path to log-file
    :param data: any text (with speaker tag)
    :return: None
    """
    with open(file_path, 'a') as f:
        f.write(data)


def write_logs_json(
    file_path: str,
    role: Literal['assistant', 'system', 'user'],
    content: str):
    """
    Append data to the prompt json log-file
    :param file_path: path to log-file
    :param role:
    :param content:
    :return: None
    """
    if role != 'system':
        with open(file_path, 'r') as fr:
            messages = json.load(fr)
    else:
        messages = []
    messages.append({'role': role, 'content': content.replace('\n', ' ').strip()})
    with open(file_path, 'w') as fw:
        json.dump(messages, fw)


def call_openapi(
    prompt_path,
    model_engine: str = "text-davinci-003",
    is_summary: bool = False,
    prompt: str = None
):

    if prompt is None:
        with open(prompt_path, 'r') as f:
            prompt = f.read()

    if is_summary:
        with open('summary.txt', 'r') as f:
            task_description = f.read()
        prompt = prompt.split("Client:", maxsplit=1)[1]
        prompt = task_description + "Client:" + prompt
        # prompt = prompt.replace('Coach:', "Me:").replace("Client:", "You:")

    is_not_successful: bool = True
    # print(prompt)
    max_tokens = 2048 if model_engine == "text-davinci-003" else int(2048 - estimate_tokens(prompt) - 10)
    print(f"{estimate_tokens(prompt)=}")
    while is_not_successful:
        try:
            response = openai.Completion.create(
                # model_engine="text-davinci-003",
                model=model_engine,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                n=1,
                stop=["Client:"]
                # stop=["\r"]  # check how stop works
            )
            is_not_successful = False
        # except openai.error.RateLimitError:
        #     print("openai server failed; retrying in a sec")
        #     time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(2)
    return response['choices'][0]['text'].strip()


def build_prompt_from_json(
    messages: list[dict]
) -> str:
    """
    ChatGPT logs into OpenAI-built conversation
    :param messages: list of log dicts
    :return:
    """
    text = ''
    for entity in messages:
        role = entity.get('role')
        content = entity.get('content')
        if role:
            if role == 'user':
                text += 'Client: '
            elif role == 'assistant':
                text += 'Coach: '
        text += content
        text += '\n'
    return text.strip()


def call_chatgpt(
    prompt_path,
    model_engine: str = 'gpt-3.5-turbo',
    is_summary: bool = False,
    messages: Optional[dict] = None
):
    if messages is None:
        with open(prompt_path, 'r') as f:
            messages = json.load(f)

    if is_summary:
        call_openapi(
            prompt_path='',
            is_summary=True,
            prompt=build_prompt_from_json(messages)
        )

    is_not_successful: bool = True
    while is_not_successful:
        try:
            response = openai.ChatCompletion.create(
                # model_engine="text-davinci-003",
                model=model_engine,
                messages=messages
            )
            is_not_successful = False
        except openai.error.RateLimitError:
            print("openai server failed; retrying in a sec")
            time.sleep(1)
    return response['choices'][0].message.content.strip()


def voice2text(fpath: str) -> str:
    result = model.transcribe(fpath)
    return result['text']


def convert_audio(
    fpath: str,
    from_: str = "ogg",
    to_: str = "mp3"
):
    mp3path = fpath.rsplit('.', maxsplit=1)[0] + "." + to_
    os.system(
        "ffmpeg -i {} -acodec libmp3lame {}"
    )
    os.remove(fpath)
    return mp3path


def voice_generate(
    text: str,
    filename: str,
    voice_id: str = "EXAVITQu4vr4xnSDxMaL",
    xi_api_key: str = os.getenv('ELEVEN_API_KEY')
) -> bool:
    """
    Get a text and send requests to api.elevenlabs.io
    :param text:
    :param filename:
    :param voice_id:
    :param xi_api_key:
    :return: filepath of saved voicing
    """
    root = "https://api.elevenlabs.io"
    response = requests.post(
        url=root + "/v1/text-to-speech/" + voice_id,
        headers={
            'accept': "audio/mpeg",
            "xi-api-key": xi_api_key,
            'Content-Type': 'application/json'
        },
        data='{"text": "'+text+'"}'

    )
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=256):
                f.write(chunk)
        return True
    print(response.status_code)
    print(response.text)
    return False


if __name__ == '__main__':
    # print(call_openapi(
    #     r"C:\Users\arsen\PycharmProjects\chatGPT_test\logs\arsenitheunicorn-20230211_023535_prompts.log",
    #     is_summary=True
    # ))
    for i in range(9):
        with open(f'summ_logs/{i}.log', 'r') as f:
            print(i, estimate_tokens(f.read()))
