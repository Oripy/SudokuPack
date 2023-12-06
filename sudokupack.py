import os
import argparse
import re
parser = argparse.ArgumentParser()

parser.add_argument('input', type=argparse.FileType('r'), help='input filename')
parser.add_argument('output', nargs='?', help='pdf output filename - default to csv name')

args = parser.parse_args()

# url_check = re.compile(r'^(http|https):\/\/([\w.-]+)(\.[\w.-]+)+([\/\w\.-]*)*\/?$')
url_check = re.compile(r'(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})(\.[a-zA-Z0-9]{2,})?')


import fpdf
from PIL import Image

pdf = fpdf.FPDF(orientation='P', format='A4', unit='mm')
pdf.add_page()

pdf.set_font("Helvetica", "B", 14)
margins = 20
puzzle_margin = 50
pdf.set_margins(margins, margins)

column_width = 80

def puzzle_page(title, author, rules, image):
    pdf.add_page()
    pdf.image(image, margins, puzzle_margin, column_width)
    pdf.set_font("Helvetica", "B", 20)
    pdf.write(text=f'{title}\n')
    pdf.set_font("Helvetica", "I", 20)
    pdf.write(text=author)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_y(puzzle_margin)
    pdf.set_x(-(margins + column_width))
    pdf.multi_cell(column_width, None, rules)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import io
from PIL import Image

def get_image_and_rules(url):
    driver = webdriver.Chrome()
    driver.get(url)

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
    img = Image.open(io.BytesIO(image_binary))

    # Get the rest of the data from the page
    title = driver.find_element(By.CLASS_NAME, 'puzzle-title').text
    author = driver.find_element(By.CLASS_NAME, 'puzzle-author').text
    rules = driver.find_element(By.CLASS_NAME, 'puzzle-rules').text

    driver.close()
    return title, author, rules, img

lines = args.input.readlines()
for line in lines:
    print(line)
    if line == '':
        continue
    if not bool(url_check.match(line)):
        print('fail')
        continue
    puzzle_page(*get_image_and_rules(line))

filename = ''
if args.output == '':
    filename, _ = f'{os.path.splitext(args.input)}.pdf'
else:
    filename = args.output
pdf.output(filename)