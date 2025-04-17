import configparser
from urllib.parse import urlparse
import base64
import hashlib
import os
import requests

config = configparser.ConfigParser()
config.read('config.ini')

import re
emojis = re.compile(r'<[^>]+alt="([^"]+)"[^>]+>')
puzzle_type_kudamono = re.compile(r'G=([^&]+)')
puzzle_type_puzz_link = re.compile(r'\?([^\/]+)')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import io
from PIL import Image

options = Options()
options.add_argument("--headless=new")
options.add_experimental_option("detach", True)

service = Service(config['DEFAULT']['CHROME_PATH'])

driver = webdriver.Chrome(options=options, service=service)
driver.implicitly_wait(10)

def cache(data_file, image_file, real_url, title, author, rules, img, source):
    with open(data_file, "w+") as file:
        file.write(f'{real_url}\n')
        file.write(f'{title}\n')
        file.write(f'{author}\n')
        file.write(f'{source}\n')
        file.write(rules)
    Image.open(img).save(image_file)

def get_rules_from_kudamono(type):
    url = f'https://pedros.works/kudamono/pages/{type}'
    try:
        requests.get(url)
        driver.get(url)
        #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "genre-rules")))
        #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "quote")))
        rules_area = driver.find_element(By.CLASS_NAME, 'quote')
        rules = rules_area.find_element(By.TAG_NAME, 'blockquote').text;
        return rules
    except:
        return ""

def get_image_and_rules(url):
    print(f"Loading {url}")
    hashed_url = hashlib.md5(url.encode()).hexdigest()
    data_file = os.path.join(config['DEFAULT']['CACHE_PATH'], f'{hashed_url}.txt')
    image_file = os.path.join(config['DEFAULT']['CACHE_PATH'], f'{hashed_url}.png')

    if os.path.exists(data_file) and os.path.exists(image_file):
        data = open(data_file, "r").readlines()
        return data[0][:-1], data[1][:-1], data[2][:-1], ''.join(data[4:]), open(image_file, "rb"), data[3][:-1]

    driver.get(url)
    real_url = driver.current_url
    scheme, host, path, params, query, fragment = urlparse(real_url)
    source = ""

    match host:
        case "sudokupad.app" | "dev.sudokupad.app":
            print("SudokuPad link")
            # Make sure the page is loaded properly
            #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'dialog')))
            #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'svgrenderer')))

            # Hide SvenPeek so it does not appear on the screenshot
            driver.execute_script('document.getElementById("svenpeek").remove()')

            # Acknowledges the dialog
            dialog = driver.find_element(By.CLASS_NAME, 'dialog')
            dialog.find_element(By.CSS_SELECTOR, 'button').click()

            # Screenshot the puzzle image
            image_binary = driver.find_element(By.ID, 'svgrenderer').screenshot_as_png
            img = io.BytesIO(image_binary)

            # Get the rest of the data from the page
            title = driver.find_element(By.CLASS_NAME, 'puzzle-title').text
            author = driver.find_element(By.CLASS_NAME, 'puzzle-author').text[4:] # Remove " by " at the begining of the Author name
            rules = driver.find_element(By.CLASS_NAME, 'puzzle-rules').get_attribute("innerHTML")
            rules = rules.replace("<br>", "")
            rules = emojis.sub(r"\1", rules)
            cache(data_file, image_file, real_url, title, author, rules, img, source)
            return real_url, title, author, rules, img, source

        case "swaroopg92.github.io":
            print("Penpa+ link")
            # Make sure the page is loaded properly
            #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'canvas')))
            puzzleinfo = driver.find_element(By.ID, 'puzzleinfo')

            title = puzzleinfo.find_element(By.ID, 'puzzletitle').text
            author = puzzleinfo.find_element(By.ID, 'puzzleauthor').text
            canvas = driver.find_element(By.ID, 'canvas')
            canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
            canvas_png = base64.b64decode(canvas_base64)
            img = io.BytesIO(canvas_png)

            # Opens the rules
            puzzleinfo.find_element(By.ID, 'puzzlerules').click()

            rules_div = driver.find_element(By.ID, 'swal2-html-container')
            rules = rules_div.find_element(By.CLASS_NAME, 'info').text
            cache(data_file, image_file, real_url, title, author, rules, img, source)
            return real_url, title, author, rules, img, source

        case "pzv.jp" | "puzz.link":
            print("puzz.link link")
            # Make sure the page is loaded properly
            #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'divques')))

            title = driver.title.split(" player")[0]
            author = ""
            type = puzzle_type_puzz_link.search(real_url).group(1)
            image_binary = driver.find_element(By.ID, 'divques').screenshot_as_png
            img = io.BytesIO(image_binary)
            rules = get_rules_from_kudamono(type)
            if rules == "":
                print("Warning: Rules not found")
            else:
                source = f'https://pedros.works/kudamono/pages/{type}'
            cache(data_file, image_file, real_url, title, author, rules, img, source)
            return real_url, title, author, rules, img, source

        case "pedros.works":
            print("Kudamono link")
            # Make sure the page is loaded properly
            #WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'papuzz')))

            papuzz = driver.find_element(By.ID, 'papuzz')
            driver.execute_script("arguments[0].setAttribute('style',arguments[1])",papuzz, 'background:white;')

            image_binary = papuzz.find_element(By.ID, 'puzzle').screenshot_as_png
            img = io.BytesIO(image_binary)

            title = driver.find_element(By.ID, 'reactio12').text
            author = driver.find_element(By.ID, 'reactio14').text

            type = puzzle_type_kudamono.search(real_url).group(1)
            rules = get_rules_from_kudamono(type)
            source = f'https://pedros.works/kudamono/pages/{type}'
            cache(data_file, image_file, real_url, title, author, rules, img, source)
            return real_url, title, author, rules, img, source

        case _:
            print("link type not supported")
            return real_url, "", "", "", Image.new("RGB", (100, 100), (255, 255, 255)), source

if __name__ == '__main__':
    pass
