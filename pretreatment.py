import time
import re
import aifuncs
from typing import Optional, Union
from myclasses import UserData, UserActive
import os
import json

with open('config/prompt_instructions.json', 'r') as f:
    prompt_instructions: dict = json.load(f)
del f


def read_prompt(
    prompt_path,
    user_active,
    step_id
):
    with open(prompt_path, 'r') as f:
        prompt: str = f.read().format(
            [getattr(user_active.user_data, attr_name) for attr_name in prompt_instructions[step_id]['fmt']]
        )
    return prompt


def yes_or_no(answer: str) -> bool:
    prompt = """Evaluate the following statement if it is a 'yes' or a 'no'. 
    Answer in a single word, only 'yes' or 'no'. Statement = {}"""

    output = aifuncs.call_openapi(
        prompt_path=None,
        prompt=prompt.format(answer)
    )
    print(f"{output=}")
    if re.search('yes', output.lower()):
        return True
    return False


def extract_info(
    info_needed: str,
    answer: str,
):
    prompt = """You will recieve a statement. 
    I need you to extract some Key information out of it and reformulate it as a thesis.
    Give the answer in minimum words. For example, if I ask you to get a name - answer with only this name.
    Don't answer in full sentences.
    
    Statement = {}
    
    Information = {}
    """
    output = aifuncs.call_openapi(
        prompt_path=None,
        prompt=prompt.format(answer, info_needed)
    )
    return output


def step_call(
    user_active: UserActive
):
    step_id: str = str(user_active.pretreatment_step).replace('.0', '')
    prompt_path: str = './prompts/' + [x for x in os.listdir('./prompts') if x.startswith(step_id + "_")][0]

    prompt = read_prompt(prompt_path, user_active, step_id)
    print('trying to call ', step_id)
    print(f"{prompt = }")
    answer = aifuncs.call_openapi(
        prompt_path='',
        prompt=prompt
    )
    print('called successfully', step_id)
    return answer

#
# def pretreatment_manager(
#     ua: UserActive,
#     func: object
# ):
#     step_n = ua.pretreatment_step
#     text = step_call(ua, step_n)
#     if step_n == 2 or step_n == 5:
#

