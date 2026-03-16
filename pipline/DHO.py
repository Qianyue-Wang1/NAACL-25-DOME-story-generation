# -*- coding: utf-8 -*-

# from dotenv import load_dotenv, find_dotenv
# _ = load_dotenv(find_dotenv()) # read local .env file
from http import HTTPStatus
import dashscope
from prompt import PROMPT_TEMPLATE
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
import logging
import dashscope
from prompt import PROMPT_TEMPLATE
from openai import OpenAI
from promptwritting import PROMPT_TEMPLATE_WRITE
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
import MEM as MindMap
from neo4j import GraphDatabase, basic_auth
import json
import re
import sys
from pathlib import Path
import random
from time import sleep

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.settings import (
    OPENAI_BASE_URL,
    OPENAI_API_KEY,
    temp_story_txt_path,
    total_story_txt_path,
)

logger = logging.getLogger(__name__)

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
                messages=messages,
            )
        except Exception as e:
            last_error = e
            wait_seconds = min(base_delay * (2 ** attempt), 8) + random.uniform(0, 0.5)
            print(f"请求失败，第{attempt + 1}/{max_retries}次重试，错误信息: {e}")
            sleep(wait_seconds)
    print(f"请求最终失败，错误信息: {last_error}")
    return None


def chatg(prompt):
    completion = chat_completion_with_retry(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a fiction expert, good at writing captivating novels"},
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

# print(chatg("what is machine learning?"))
def data_process_outline(text):
    chapters = text.strip().split("\n\n")

    # 创建一个空字典来存储章节
    chapter_dict = {}

    # 遍历拆分后的章节
    for chapter in chapters:
        # 进一步拆分章节标题和内容
        parts = chapter.split("\n")
        chapter_number = parts[0].split(" ")[1].split(":")[0]  # 提取章节号
        chapter_title = parts[0].split(": ")[1]  # 提取章节标题
        chapter_content = "\n".join(parts[1:])  # 提取章节内容
        # 将章节号、标题和内容存储在字典中
        chapter_dict[chapter_number] = {
            "title": chapter_title,
            "content": chapter_content
        }
    return chapter_dict

def data_process_json(text):
    #将json string 转为元素是dic的list
    
    
    #q:text的开头和结尾是```json 和```，需要去掉，编写代码实现
    #a:使用strip()函数去掉
    text=text.strip("`")
    text=text.strip("json")
    text=text.strip(" ")
    logger.info(text)
  
    list_object = json.loads(text) 
    return list_object

def re_detail_outline(text):
    # 正则表达式来提取相关信息
    pattern = "Outline of chapter \d+:\s*\n(.*?)(?=\s*$)"
    # 在文本中搜索匹配的部分
    match = re.search(pattern, text, re.DOTALL)
    if match:
        # 输出提取到的内容
        print(match.group(1))
    else:
        print("No matching text found.")

def re_story(text):
    # 正则表达式来提取相关信息
    pattern = "Story:\s*\n(.*?)(?=\s*$)"
    # 在文本中搜索匹配的部分
    match = re.search(pattern, text, re.DOTALL)
    if match:
        # 输出提取到的内容
        print(match.group(1))
    else:
        print("No matching text found.")

# def re_chapter_outline(text):
#     # 正则表达式编译，包括re.DOTALL以使得.可以匹配换行符
#     pattern = re.compile(r"- Chapter Outline (\d+):\s*\n\s*(.+?)(?=\n- Chapter Outline |\Z)", re.DOTALL)



#     # 使用findall方法查找所有匹配项
#     matches = pattern.findall(text)

#     # 打印结果
#         # for match in matches:
#         #     print(f"Chapter {match[0]} outline is:\n{match[1]}\n")
#     print(matches[0])
#     return matches[0][0],matches[0][1]

# def re_chapter_outline(text):
#     spattern=re.compile(":")
#     res=spattern.split(text)
#     outlines=[]
#     for i in range(len(res)):
#         if i==0:
#             continue
#         else:
#             if i==len(res)-1:
#                 outlines.append(res[i])
#             else:

#                 outlines.append(res[i][:(-19)])

#     print(outlines)
    
#     return outlines

def re_chapter_outline(text):
    # Chapter Outline 1: ...
    # Outline of chapter 1: ...
    pattern = re.compile(
        r"(?:^|\n)\s*(?:Chapter Outline|Outline of chapter)\s*\d+\s*:\s*(.*?)(?=(?:\n\s*(?:Chapter|Outline of chapter)\s*\d+\s*:)|\Z)",
        re.IGNORECASE | re.DOTALL
    )
    outlines = [m.strip() for m in pattern.findall(text) if m.strip()]

    # 兜底：按空行切分
    if not outlines:
        outlines = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    logger.info(f"parsed outlines count={len(outlines)}")
    return outlines

def data_process_json(text):
    #将json string 转为元素是dic的list
    #q:text的开头和结尾是```json 和```，需要去掉，编写代码实现
    #a:使用strip()函数去掉
    text=text.strip("`")
    text=text.strip("json")
    text=text.strip(" ")
    
  
    list_object = json.loads(text) 
    return list_object


# Chapter contains: stage, storyline
def story_writting(chapter,total_content,step,near_info,driver,title):
        
    last_chapter_story = near_info
    chapter_outline_prompt = 'chapter_outline'
    story_prompt = 'write_en'
    
    line_outline_prompt_t=PROMPT_TEMPLATE_WRITE[chapter_outline_prompt]
    content_prompt_t=PROMPT_TEMPLATE_WRITE[story_prompt]

    stage = chapter["stage"]
    volume_outline = chapter["storyline"]
    detail_outline = []

    
    history= MindMap.find_relevant_info(volume_outline,step,title,driver)

    logger.info("="*20)
    logger.info(f"stage:{stage}")
    logger.info(f"volume_outline:{volume_outline}")
    logger.info(f"volume history:{history}")
    logger.info("="*20)
    
    po=(ChatPromptTemplate.from_template(line_outline_prompt_t)).format_messages(
                                                                                volume_outline=volume_outline,
                                                                                last_chapter=last_chapter_story,
                                                                                history=history)           
    
    c=0
    outlines=[]
    while(True):
        try:
            outline = chat(po[0].content) # TODO

            outlines = re_chapter_outline(outline)
            logger.info("there are outlines for the volume")
            for i in outlines:
            
                logger.info(f"outline :{i}")

            c=True
            for i in outlines:
                if len(i)<90:
                    c=False
                    break
            if not(c):
                continue
            else:
                break
            
            if len(outlines[1])>=50:
                break
            import time
            time.sleep(1)
            
        except Exception as e:
            c+=1
            if c>5:
                
                assert RuntimeError(" too many try!!!")

            logger.exception("error:" + str(e))
            import time
            time.sleep(1)
            continue
    for i in range(len(outlines)):
        
        
        outline=outlines[i]
        
        detail_outline.append(outline)
        
        
        
        cntent_prompt_tempate =ChatPromptTemplate.from_template(content_prompt_t)
        history= MindMap.find_relevant_info(volume_outline,step,title,driver)
        
        pw=cntent_prompt_tempate.format_messages(
                                                    volume_outline=volume_outline,
                                                    chapter_outline=outline,
                                                    last_chapter=last_chapter_story,
                                                    history=history)
        story_content=chat(pw[0].content) # TODO
        
        last_chapter_story = story_content
        
        MindMap.set_history(story_content,driver,title,step)
        
        total_content.append(story_content)
        path = temp_story_txt_path(title)
        with open(path, 'a') as f:
            f.write(story_content)       
    
    return total_content,last_chapter_story
           
      
        

