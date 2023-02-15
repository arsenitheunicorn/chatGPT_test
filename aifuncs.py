import os
import time
import requests
import openai
import whisper


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


def call_openapi(
    prompt_path,
    model_engine: str = "text-davinci-003",
    is_summary: bool = False,
    prompt: str = None
):
    # if add_prompt:
    #     with open('prompt.txt', 'r') as f:
    #         prompt = f.read() + '\n' + prompt  # .replace('\n', ' ')

    if prompt is None:
        with open(prompt_path, 'r') as f:
            prompt = f.read()

    if is_summary:
        with open('summary.txt', 'r') as f:
            task_description = f.read()
        prompt = prompt.split("Patient:", maxsplit=1)[1]
        prompt = task_description + "Patient:" + prompt
        # prompt = prompt.replace('Coach:', "Me:").replace("Patient:", "You:")

    is_not_successful: bool = True
    # print(prompt)

    while is_not_successful:
        try:
            response = openai.Completion.create(
                # model_engine="text-davinci-003",
                model=model_engine,
                prompt=prompt,
                max_tokens=2048,
                temperature=0.6,
                n=1,
                stop=["Patient:"]
                # stop=["\r"]  # check how stop works
            )
            is_not_successful = False
        except openai.error.RateLimitError:
            print("openai server failed; retrying in a sec")
            time.sleep(1)
    return response['choices'][0]['text'].strip()


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
    print(call_openapi(
        r"C:\Users\arsen\PycharmProjects\chatGPT_test\logs\arsenitheunicorn-20230211_023535_prompts.log",
        is_summary=True
    ))
