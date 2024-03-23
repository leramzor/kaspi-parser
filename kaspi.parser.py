import os
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import telebot
from telebot.types import Message

bot = telebot.TeleBot('6205042656:AAHqGIsWzaQQDA7Ty8HuBAbfOVoivN5x-Fs')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Пришлите мне ссылку для поиска магазина Kaspi, и я скопирую данные о товаре и отправлю их вам обратно в виде файла Excel.")

@bot.message_handler(func=lambda message: True)
def scrape_kaspi(message: Message):
    base_url = message.text.strip()
    if not base_url.startswith("https://kaspi.kz/shop/"):
        bot.reply_to(message, "Недопустимая ссылка. Пожалуйста, пришлите ссылку на магазин Kaspi.")
        return
    data = []
    page=1
    first_page_url = base_url +'?page=' +str(page)
    while True:
        
        driver = webdriver.Firefox()
        driver.get(base_url)
        if driver.current_url == first_page_url:
            break
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        if response.status_code == 200:
            products_section = soup.find("div", class_="search-result mount-search-result")

            product_items = products_section.find_all("div", class_="item-card ddl_product ddl_product_link undefined")

            for product_item in product_items:
                product_name = product_item.find("div", class_="item-card__name").text
                product_price = product_item.find("div", class_="item-card__debet")
                price = product_price.find("span", class_="item-card__prices-price").text
                rating_span = product_item.find("span", {'class':re.compile(r'rating _small _\d+')})
                if rating_span is not None:
                    rating_class = rating_span['class'][-1]  # get the last class name
                    rating = re.search(r'\d+', rating_class).group()  # extract the digits from the class name
                else:
                    rating = ' '
                item_link = product_item.find("a", class_="item-card__name-link")
                driver.get(item_link['href'])
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "sellers-table__self")))
                htmls = driver.page_source

                soups = BeautifulSoup(htmls, "html.parser")

                article = soups.find("div", class_="item__sku").text
                image=soups.find("div", class_="item__slider-pic-wrapper")
                item_image=image.find('img')
                sellers_table = soups.find("table", class_="sellers-table__self")

                sellers_rows = sellers_table.find_all("tr") if sellers_table is not None else []
                seller_prices = sellers_table.select('div.sellers-table__price-cell-text:not([class*="_installments-price"])') if sellers_table is not None else []
                sellers = []
                for sellers_row, seller_price in zip(sellers_rows, seller_prices):
                    name_tag = sellers_row.find('a')
                    if len(sellers) == 5:
                        break
                    if name_tag is None:
                        continue
                    seller = name_tag.get_text().strip()
                    itemimage= item_image['src']
                    rating_seller_span = sellers_row.find("div", {'class':re.compile(r'rating _seller _\d+')})
                    if rating_seller_span is not None:
                        rating_s_class = rating_seller_span['class'][-1]  # get the last class name
                        rating_sel = re.search(r'\d+', rating_s_class).group()  # extract the digits from the class name
                    else:
                        rating_sel = ' '
                    if seller in [s[0] for s in sellers]:
                        continue
                    seller_price = seller_price.text
                    sellers.append([seller, seller_price,rating_sel])
                while len(sellers) < 5:
                    sellers.append(['', ''])
                item = [product_name, article, price,rating, itemimage] + [s for seller in sellers for s in seller]
                data.append(item)
        
                driver.back()
            page+=1
            if url == first_page_url:
                break
        else:
            break
            
    df = pd.DataFrame(data, columns=["Product Name","Article", "Price","Item_rating","Image","Продавец1","Price seller1","Rating1","Продавец2","Price seller2","Rating2","Продавец3","Price seller3","Rating3","Продавец4","Price seller4","Rating4","Продавец5","Price seller5"])
    excel_file_name = 'products.xlsx'
    df.to_excel(excel_file_name, index=False)
    time.sleep(50)
    with open(excel_file_name, 'rb') as f:
        bot.send_document(message.chat.id, f)
        
    os.remove(excel_file_name)
bot.polling()