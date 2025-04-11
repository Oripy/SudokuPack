import configparser
from urllib.parse import urlparse
import base64

config = configparser.ConfigParser()
config.read('config.ini')

import re
emojis = re.compile(r'<[^>]+alt="([^"]+)"[^>]+>')

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

def get_image_and_rules(url):
    print(f"Loading {url}")
    driver.get(url)

    scheme, host, path, params, query, fragment = urlparse(driver.current_url)

    match host:
        case "sudokupad.app" | "dev.sudokupad.app":
            # Make sure the page is loaded properly
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'dialog')))
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'svgrenderer')))

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
            return title, author, rules, img

        case "swaroopg92.github.io":
            # Make sure the page is loaded properly
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'canvas')))
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
            return title, author, rules, img

        case "pzv.jp" | "puzz.link":
            # Make sure the page is loaded properly
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'divques')))

            title = driver.title.split(" player")[0]
            author = ""
            rules = ""
            image_binary = driver.find_element(By.ID, 'divques').screenshot_as_png
            img = io.BytesIO(image_binary)
            return title, author, rules, img

        case "pedros.works":
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'papuzz')))

            papuzz = driver.find_element(By.ID, 'papuzz')
            driver.execute_script("arguments[0].setAttribute('style',arguments[1])",papuzz, 'background:white;')

            image_binary = papuzz.find_element(By.ID, 'puzzle').screenshot_as_png
            img = io.BytesIO(image_binary)

            title = driver.find_element(By.ID, 'reactio12').text
            author = driver.find_element(By.ID, 'reactio14').text

            help_button = driver.find_element(By.CLASS_NAME, 'help')
            help_button.click()
            
            rules_area = driver.find_element(By.CLASS_NAME, 'quote')
            rules = rules_area.find_element(By.TAG_NAME, 'blockquote').text;
            
            return title, author, rules, img

        case _:
            return "", "", "", Image.new("RGB", (100, 100), (255, 255, 255))

if __name__ == '__main__':
    pass
