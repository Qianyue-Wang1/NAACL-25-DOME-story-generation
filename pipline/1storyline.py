# -*- coding: utf-8 -*-
#premise׫дstoryline
import datetime

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from http import HTTPStatus
from openai import OpenAI
from promptwritting import PROMPT_TEMPLATE_WRITE
from langchain.chat_models import ChatOpenAI

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

#
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from http import HTTPStatus
from openai import OpenAI
from promptwritting import PROMPT_TEMPLATE_WRITE
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate,LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from neo4j import GraphDatabase, basic_auth
import json
from time import sleep
from logger import *
import json
import re
import pandas as pd
import os
import sys
from pathlib import Path
import random

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.settings import (
    DATA_DIR,
    STORY_INPUT_CSV,
    title_dir,
    roughoutline_txt_path,
    roughoutline_json_path,
    OPENAI_BASE_URL,
    OPENAI_API_KEY,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


def chat_completion_with_retry(model, messages, max_retries=5, base_delay=1.0):
    last_error = None
    for attempt in range(max_retries):
        try:
            client = OpenAI(
                base_url=OPENAI_BASE_URL,
                api_key=OPENAI_API_KEY,
            )
            return client.chat.completions.create(
                model=model,
                messages=messages
            )
        except Exception as e:
            last_error = e
            wait_seconds = min(base_delay * (2 ** attempt), 8) + random.uniform(0, 0.5)
            logger.warning(f"请求失败，第{attempt + 1}/{max_retries}次重试，错误信息: {e}")
            sleep(wait_seconds)
    logger.error(f"请求最终失败，错误信息: {last_error}")
    return None

def chatg(prompt):
    completion = chat_completion_with_retry(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a novelist who specializes in writing science fiction that is logically rigorous and reasonably safe"},
            {"role": "user", "content": prompt}
        ],
        max_retries=5,
        base_delay=1.0
    )
    if completion is None:
        return None
    return completion.choices[0].message.content



def chat(prompt):
    messages = [
        {"role": "system",
             "content": "You are a novelist who specializes in writing science fiction that is logically rigorous and reasonably safe"},
        {'role': 'user', 'content': prompt}]

    response = chat_completion_with_retry(
        model="gpt-3.5-turbo",
        messages=messages,
        max_retries=5,
        base_delay=1.0
    )
    if response is None:
        return None
    return response.choices[0].message.content

def data_process_json(text):
    
    text=text.strip("`")
    text=text.strip("json")
    text=text.strip(" ")
    logger.info(text)
  
    list_object = json.loads(text) 
    return list_object



if __name__ == '__main__':

    stage_schema = ResponseSchema(name="stage",
                             description="Was the phase in the development of a story, named after the stage names provided in the novel theory.It is an json object containing all chapter numbers and chatpter summary that belong to it.")
    storyline_schema = ResponseSchema(name="storyline",
                                        description="Was a string that describes the storyline of the stage based on the story theory and other provided information.")

    response_schemas = [stage_schema,
                        storyline_schema]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    print(format_instructions)

    df = pd.read_csv(STORY_INPUT_CSV)
    #read the csv file by setting ,character,plot requirement
    #we follow the input setting of DOC and RE3,you can refer to https://github.com/yangkevin2/emnlp22-re3-story-generation to get input
    settings=df['setting'].tolist()
    characters=df['character'].tolist()
    plot_requirements=df['plot requirement'].tolist()
    theory="""
    1. Exposition: The story begins in a set setting, introducing the main characters and the setting of the story. The main character usually lives in an environment that they consider ordinary or normal, but that environment sets the basis for the development of the story.\n
    2. Rising Action: An event or conflict is introduced in the story that forces the main character out of their comfort zone and begins to face a series of challenges or conflicts. These events move the story forward, gradually increasing the tension and complexity of the story.\n
    3. Climax: This is the most tense and exciting moment in the story when the main characters face their main conflict or challenge. This is often a turning point in the story, where the actions of the main character will determine the final course of the story.\n
    4. Falling Action: After the climax, the story begins to transition to the ending. The main character begins to deal with the aftermath of the climax, conflicts are resolved, and the tension of the story gradually decreases.\n
    5. Denouement or Resolution: the conflict of the story is resolved and all outstanding questions are answered. The fate of the main character and other characters is clarified, and the story reaches a satisfying conclusion. This stage not only resolves the external conflicts of the story, but also shows the inner changes and growth of the main character.\n
   
"""
    format_instructions=format_instructions

    # count=1
    # for setting,character,outline in zip(settings,characters,plot_requirements):
    #     title=str(count)
    #     path = chapter_dir(title)

    #     if not os.path.exists(path):
    #         print("yes")
    #         os.makedirs(path)
    
    #     from promptwritting import PROMPT_TEMPLATE_WRITE
    #     stryline_prompt_t=PROMPT_TEMPLATE_WRITE['storyline']
    #     stryline_prompt_tempate =ChatPromptTemplate.from_template(template=stryline_prompt_t)
    #     ps=stryline_prompt_tempate.format_messages(theory=theory,setting=setting,character=character,outline=outline,format=format_instructions)
    #     storyline= chat(ps[0].content)

    
    #     while(1):
    #         print(storyline)
    #         if '[' in storyline and ']' in storyline:
    #             print("storyline is correct")
    #             break
    #         else:
    #             print("try again")
    #             storyline= chat(ps[0].content)
    #             count+=1
    #             if count>5:
    #                 print("try too many times")
    #                 break
                
    #     with open(storyline_txt_path(title), 'w') as file:
    #         file.write(storyline)

    #     #chage text to json object
    #     json_storyline=data_process_json(storyline)
    #     #保存json文件
    #     with open(storyline_json_path(title), 'w') as file:
    #         json.dump(json_storyline, file)

#     all_storylines = []

# for idx, (setting, character, outline) in enumerate(zip(settings, characters, plot_requirements), start=1):
#     title = str(idx)
#     path = chapter_dir(title)
#     os.makedirs(path, exist_ok=True)

#     from promptwritting import PROMPT_TEMPLATE_WRITE
#     stryline_prompt_t = PROMPT_TEMPLATE_WRITE['storyline']
#     stryline_prompt_tempate = ChatPromptTemplate.from_template(template=stryline_prompt_t)
#     ps = stryline_prompt_tempate.format_messages(
#         theory=theory, setting=setting, character=character, outline=outline, format=format_instructions
#     )
#     storyline = chat(ps[0].content)

#     retry = 0
#     while True:
#         if storyline and '[' in storyline and ']' in storyline:
#             break
#         retry += 1
#         if retry > 5:
#             print("try too many times")
#             break
#         storyline = chat(ps[0].content)

#     # 保存原始文本
#     with open(storyline_txt_path(title), 'w', encoding='utf-8') as file:
#         file.write(storyline or "")

#     # 转为 JSON（若解析失败则保存为空列表）
#     try:
#         json_storyline = data_process_json(storyline)
#     except Exception:
#         json_storyline = []

#     with open(storyline_json_path(title), 'w', encoding='utf-8') as file:
#         json.dump(json_storyline, file, ensure_ascii=False, indent=2)

#     all_storylines.append(json_storyline)  

# # 循环结束后统一写总纲
# with open(ROUGH_OUTLINE_JSON, 'w', encoding='utf-8') as f:
#     json.dump(all_storylines, f, ensure_ascii=False, indent=2)

    for i in range(len(df)):
        # 生成第i篇的log名称并添加相关句柄
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f"{i}_{now}_storyline.txt" 
        log_path = os.path.join(DATA_DIR,"log",filename)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8', delay=False)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info("="*20)
        logger.info(f"Start to generate story {i+1}")
        logger.info("="*20)
        #读取每一行的数据
        title=str(i+1)
        story_path=title_dir(title)
        if not os.path.exists(story_path):
                os.makedirs(story_path)

        setting=df.iloc[i,0]#
        character=df.iloc[i,1]#
        outline=df.iloc[i,2]#
        logger.info("="*20)
        logger.info("Current Premise")
        logger.info(f"setting:{setting}")
        logger.info(f"character:{character}")
        logger.info(f"outline:{outline}")
        logger.info("="*20)   

        from promptwritting import PROMPT_TEMPLATE_WRITE
        stryline_prompt_t = PROMPT_TEMPLATE_WRITE['storyline']
        stryline_prompt_tempate = ChatPromptTemplate.from_template(template=stryline_prompt_t)
        ps = stryline_prompt_tempate.format_messages(
            theory=theory, setting=setting, character=character, outline=outline, format=format_instructions
        )
        storyline = chat(ps[0].content)

        retry = 0
        while True:
            if storyline and '[' in storyline and ']' in storyline:
                break
            retry += 1
            if retry > 5:
                logger.warning("try too many times")
                break
            storyline = chat(ps[0].content)

        # 保存原始文本
        with open(roughoutline_txt_path(title), 'w', encoding='utf-8') as file:
            file.write(storyline or "")

        # 转为 JSON（若解析失败则保存为空列表）
        try:
            json_storyline = data_process_json(storyline)
        except Exception:
            json_storyline = []

        with open(roughoutline_json_path(title), 'w', encoding='utf-8') as file:
            json.dump(json_storyline, file, ensure_ascii=False, indent=2)    

        for h in logger.handlers:
            try:
                h.flush()
            except Exception:
                pass
        logger.removeHandler(file_handler)
        file_handler.close()
        


