# -*- coding: utf-8 -*-
"""Document_type_checker.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12NKU6QK9KYgdtuZWcV2YxMHwCyMx46BD

# Импорт библиотек
"""

import base64
import json
from pathlib import Path
import re
import os

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pandas.io.json import json_normalize

import requests

import matplotlib.pyplot as plt

from striprtf.striprtf import rtf_to_text

from pymystem3 import Mystem

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, recall_score, precision_score, classification_report, confusion_matrix, ConfusionMatrixDisplay

import pickle

"""# Функции чтения файлов"""

def get_full_RTFtext(filename):      # Функция для чтения .rtf файлов 
    with open(filename) as infile:
        content = infile.read()
        text = rtf_to_text(content)

    return text

def get_text(filename):               # Функция для чтения всех остальных файлов 
    with open(filename, 'rb') as f:
        encoded = base64.b64encode(f.read())

    ext = Path(filename).suffix[1:]
    if ext == 'rtf':
        return get_full_RTFtext(filename)

    url = 'http://localhost:8080/textract'
    myobj = {
        'data': encoded.decode('utf-8'),
        'file_type': ext
    }

    x = requests.post(url, json = myobj)

    if x.status_code != 200:
        return None
        
    return json.loads(x.text)['text']

"""# Препроцессинг"""

def normalize(text):
    mystem = Mystem()

    tokens = mystem.lemmatize(text)
    tokens = [token for token in tokens if
              token not in [" ", '\n'] \
              ]
    text = ' '.join(tokens)
    return text


def preprocess(my_string, verbose=True):
    if verbose:
        print('-', end='')
    
    my_string = re.sub(r"http\S+", "", my_string)
    my_string = re.sub(r'(\!)(.*?)\.((png)|(jpg)|(jpeg))', "", my_string)
    my_string = re.sub(r'(\{color)(.*?)\}', "", my_string)
    my_string = re.sub(r'.*?\!(.*)!.*', "", my_string)
    
    my_string = my_string.lower().strip()

    my_string = re.sub(r'[^\w\s]', ' ', my_string)
    my_string = re.sub(r'\n', ' ', my_string)
    my_string = re.sub(r'[0-9]+', '', my_string)
    my_string = re.sub(r'  *', ' ', my_string)
    my_string = my_string.strip()
    my_string = normalize(my_string)
    my_string = re.sub( r'  *', ' ', my_string)
    my_string = ' '.join([el for el in my_string.strip().split() if len(el) > 1])
    my_string = my_string.replace('_', '')
    
    return my_string

def read(filepath):
    text = get_text(filepath).replace('\n', ' ')
    return text

"""# DocumentTypeChecker: бот

Загрузка обученных моделей
"""

tfidf = pickle.load(open('D:/Downloads/hacka/tfidf.pkl', 'rb')) # загрузка tfidf
model = pickle.load(open('D:/Downloads/hacka/logistic_model.pkl', 'rb'))# загрузка LogisticRegression
le = pickle.load(open('D:/Downloads/hacka/LabelEncoder.pkl', 'rb'))# загрузка LabelEncoder

import random
from collections import defaultdict

with open('C:/Users/Павел/Downloads/Telegram Desktop/keyphrases2.txt', encoding='utf-8') as f:
    keyphrases = f.readlines()

processed_keyphrases = preprocess(' ддд '.join(keyphrases)).split(' ддд ')

proc2orig = defaultdict(list)
for idx, keyph in enumerate(processed_keyphrases):
    proc2orig[keyph].append(keyphrases[idx].strip())

def get_orig_from_processed(words, text):
    orig_words = []
    for word in words:
        for orig_word in proc2orig[word]:
            if orig_word in text:
                orig_words.append(orig_word)
                break
    return orig_words

def find_ngrams(input_list, n):
    return zip(*[input_list[i:] for i in range(n)])

def get_context_from_words(phrases, text, context_window=2):
    result = []
    tokens = text.split()
    for phrase in phrases:
        phrase_words = phrase.split()
        for idx, ngram in enumerate(find_ngrams(tokens, len(phrase_words))):
            if list(ngram) == phrase_words:
                span_begin = max(0, idx - context_window)
                span_end = min(len(tokens), idx + len(phrase_words) + context_window)
                result.append(' '.join(tokens[span_begin:span_end]))
    result = random.sample(result, k=min(10, len(result)))
    return result

def end2end(filepath):                                # функция результата визуализации
    orig_text = read(filepath)
    text = preprocess(orig_text, verbose=False)
    vec = tfidf.transform([text])
    
    result = {}
    result['doc_id'] = Path(filepath).stem
    result['num_class'] = model.predict(vec)[0]
    result['text_class'] = le.classes_[result['num_class']]
    result['confidence'] = model.predict_proba(vec)[0, result['num_class']]
    

    nums = vec[0].toarray() * model.coef_[result['num_class']]
    top = np.argpartition(nums, -10)[:, -10:]

    proc_words = tfidf.get_feature_names_out()[top].reshape(-1).tolist()
    orig_words = get_orig_from_processed(proc_words, orig_text)
    result['top_words'] = ', '.join(orig_words)
    result['context_phrases'] = get_context_from_words(orig_words, orig_text)
    return result

"""Реализация бота """

import telebot

TOKEN = '5776246544:AAH0RhhoPz91lIsZeRH5xpR-5kCmC4I-OAs'
URL = 'https://api.telegram.org/bot'
bot = telebot.TeleBot(TOKEN)

from telebot import types
from telebot.types import InputFile

file_cache = None
result_cache = None


@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.from_user.id, "👋 Привет! Я твой бот-помошник! Отправь мне договор для распознавания")

@bot.message_handler(content_types=['document'])
def handle_docs_doc(message):
  try:
      chat_id = message.chat.id
      file_info = bot.get_file(message.document.file_id)
      downloaded_file = bot.download_file(file_info.file_path)

      src = os.path.join('D:/Downloads/', message.document.file_name) 

      if src.split('.')[1] in ['docx','doc','rtf','pdf']: 
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
            global file_cache
            file_cache = src


        result = end2end(src)
        global result_cache
        result_cache = result

        bot.reply_to(message, f"*Документ:* {result['doc_id']}\n\n"
                              f"*Класс:* {result['text_class']}\n\n"
                              f"*Уверенность:* {np.round(result['confidence'] * 100, 2)}%\n\n"
                              f"*Ключевые слова:* {result['top_words']}", parse_mode="Markdown"
                              )
        backslash_char = "\n"
        bot.reply_to(message, f"*Ключевые фразы:*{f'{backslash_char*2}'} {f'{backslash_char*2}'.join(result['context_phrases'])}", parse_mode="Markdown")
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("👋 Отправить в обработку")
        btn2 = types.KeyboardButton("❓ Сообщить в поддержку")
        markup.add(btn1, btn2) 
        bot.send_message(message.from_user.id, "Выберите опцию", reply_markup = markup)
      
      else:
        bot.send_message(message.from_user.id, "Упс... Неверный тип файла. Выберите файл из списка допустимых расширений: DOCX, DOC, PDF, RTF")
          
  except Exception as e:
      bot.reply_to(message, e)


@bot.message_handler(content_types=['text'])
def func(message):
    global result_cache
    global file_cache
    if(message.text == "👋 Отправить в обработку"):

      if result_cache['text_class'] == 'Договоры для акселератора/Договоры оказания услуг':
        bot.send_document('@EmbedikaServiceContracts', InputFile(file_cache))
        bot.send_message(message.chat.id, text="Документ отправлен в обработку")

      elif result_cache['text_class'] == 'Договоры для акселератора/Договоры подряда':
        bot.send_document('@EmbedikaContractAgreements', InputFile(file_cache))
        bot.send_message(message.chat.id, text="Документ отправлен в обработку")

      elif result_cache['text_class'] == 'Договоры для акселератора/Договоры купли-продажи':
        bot.send_document('@EmbedikaPurchaseAndSaleAgreement', InputFile(file_cache))
        bot.send_message(message.chat.id, text="Документ отправлен в обработку")

      elif result_cache['text_class'] == 'Договоры для акселератора/Договоры аренды':
        bot.send_document('@EmbedikaLeaseAgreements', InputFile(file_cache))
        bot.send_message(message.chat.id, text="Документ отправлен в обработку")

      elif result_cache['text_class'] == 'Договоры для акселератора/Договоры поставки':
        bot.send_document('@EmbedikaSupplyContracts', InputFile(file_cache))
        bot.send_message(message.chat.id, text="Документ отправлен в обработку")

      else:
        bot.send_message(message.from_user.id, "Упс... Документ не может быть отправлен в обработку")

    elif(message.text == "❓ Сообщить в поддержку"):
      bot.send_message('@EmbedikaTechnicalSupport', f"НЕВЕРНАЯ КЛАССИФИКАЦИЯ!!!\n"
                                                    f"Документ: {result_cache['doc_id']}\n"
                                                    f"Класс: {result_cache['text_class']}\n"
                                                    f"Уверенность: {np.round(result_cache['confidence'] * 100, 2)}%\n"
                                                    f"Ключевые фразы: {result_cache['top_words']}"
                                                    )
      bot.send_document('@EmbedikaTechnicalSupport', InputFile(file_cache))
      bot.send_message(message.chat.id, text="Документ отправлен в службу поддержки")



bot.polling(none_stop=True, interval=0)