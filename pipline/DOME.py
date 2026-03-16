# -*- coding: utf-8 -*-

import datetime

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from http import HTTPStatus
import dashscope
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
from logger import *
#导入依赖�?
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from http import HTTPStatus
import dashscope
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
import MEM as MindMap
from neo4j import GraphDatabase, basic_auth
import json
from time import sleep
import DHO
import pandas as pd
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.settings import STORY_INPUT_CSV, total_story_txt_path, DATA_DIR
from config.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE

import logging

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# read the story input CSV
df = pd.read_csv(STORY_INPUT_CSV)
settings = df['setting'].tolist() if 'setting' in df.columns else []
characters = df['character'].tolist() if 'character' in df.columns else []
outlines = df['outline'].tolist() if 'outline' in df.columns else []

# iterate numeric title folders under DATA_DIR (1,2,3...)
dirs = [p for p in DATA_DIR.iterdir() if p.is_dir() and p.name.isdigit()]
dirs = sorted(dirs, key=lambda p: int(p.name))

print(f"Found {len(dirs)} title directories to process.")

for title_path in dirs:
    title = title_path.name
    storyline_file = title_path / 'rough_outline.json'
    if not storyline_file.exists():
        continue
    with open(storyline_file, 'r', encoding='utf-8') as f:
        chapter_dict = json.load(f)

    now = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"{title}_{now}_dome.txt" 
    log_path = os.path.join(DATA_DIR,"log",filename)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8', delay=False)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    root_logger.info(f"Start processing title={title}")
    for h in root_logger.handlers:
        try:
            h.flush()
        except Exception:
            pass

    driver = None
    session = None
    try:
        idx = int(title) - 1
        setting = settings[idx] if idx < len(settings) else ""
        character = characters[idx] if idx < len(characters) else ""
        outline = outlines[idx] if idx < len(outlines) else ""

        if not NEO4J_URI or not NEO4J_PASSWORD:
            raise RuntimeError(
                "缺少 Neo4j 连接配置。请在 settings 中设置 NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD。"
            )

        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=basic_auth(NEO4J_USERNAME, NEO4J_PASSWORD))

        session = driver.session()
        session.run("MATCH (n) DETACH DELETE n")

        MindMap.set_initial([setting, character, outline], driver, title)
        step = 1
        near_info = ""
        total_content = []
        for chapter in chapter_dict:
            total_content, near_info = DHO.story_writting(chapter, total_content, step, near_info, driver, title)
            root_logger.info(f"title={title}, chapter_step={step} finished")
            for h in root_logger.handlers:
                try:
                    h.flush()
                except Exception:
                    pass
            step += 1

        path = total_story_txt_path(title)
        for i in range(len(total_content)):
            with open(path, 'a', encoding='utf-8') as f:
                f.write(total_content[i])
                f.write("\n")
                f.flush()

        root_logger.info(f"title={title} finished, paragraphs={len(total_content)}")
        for h in root_logger.handlers:
            try:
                h.flush()
            except Exception:
                pass
    finally:
        if session is not None:
            session.close()
        if driver is not None:
            driver.close()
        root_logger.removeHandler(file_handler)
        file_handler.close()
