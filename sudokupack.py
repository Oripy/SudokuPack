import os
import argparse
import re
parser = argparse.ArgumentParser()

parser.add_argument('input', type=argparse.FileType('r'), help='input filename')
parser.add_argument('output', nargs='?', help='pdf output filename - default to csv name')
parser.add_argument('--ppp', type=int, default=2, help="Nbr of puzzle per page")

args = parser.parse_args()

url_check = re.compile(r'(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})(\.[a-zA-Z0-9]{2,})?')

import fpdf
from fpdf.enums import XPos, YPos
from PIL import Image

pdf = fpdf.FPDF(orientation='P', format='A4', unit='mm')
pdf.add_page()

pdf.add_font('Roboto', '', "Roboto.ttf")
pdf.add_font('Roboto-Bold', '', "Roboto-Bold.ttf")
pdf.add_font('Roboto-Italic', '', "Roboto-Italic.ttf")

pdf.set_font("Roboto-Bold", "", 14)
margins = 15
puzzle_margin = 40
offset = 135
divider_height = 5
pdf.set_margins(margins, margins)

column_width = 90
nbr_per_page = args.ppp
nbr_lines_list_first_page = 45
nbr_lines_list = 50

def title_page(title, details):
    pdf.set_font("Roboto-Bold", "", 30)
    for elem in title.split('\\n'):
        pdf.cell(0, h=10, text=elem, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("Roboto", "", 20)
    pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT, border="T")
    for i in range(len(details)):
        pdf.set_font("Roboto", "", 14)
        pdf.cell(0, h=5, text=f'{i+1} - {details[i][1]} {details[i][2]}\n', new_x=XPos.LMARGIN, new_y=YPos.NEXT, link=details[i][5])

def puzzle_page(nbr, link, title, author, rules, image):
    position = nbr%nbr_per_page
    pdf.set_y(position*(offset-divider_height)+margins)
    if position != 0:
        pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT, border="T")
    pdf.image(image, margins, position*offset+puzzle_margin, column_width, link=link)
    pdf.set_font("Roboto-Bold", "", 20)
    anchor = pdf.add_link()
    pdf.set_link(anchor, position*offset+margins)
    pdf.write(text=f'{nbr+1} - {title}\n')
    pdf.set_font("Roboto-Italic", "", 20)
    pdf.write(text=f'{author}\n')
    pdf.set_font("Roboto", "", 14)
    pdf.write(text=link, link=link)
    pdf.set_font("Roboto", "", 12)
    pdf.set_y(position*offset+puzzle_margin)
    pdf.set_x(-(margins + column_width))
    pdf.multi_cell(column_width, None, rules)
    return anchor


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

lines = args.input.read().splitlines()
pack_title = ''
details = []
for line in lines:
    print(line)
    if line == '':
        continue
    if not bool(url_check.match(line)):
        pack_title = line
        continue
    title, author, rules, img = get_image_and_rules(line)
    
    details.append([line, title, author, rules, img])

# Allow more pages for title page if it will overflow
if len(details) > nbr_lines_list_first_page:
    pdf.add_page()
for i in range((len(details)-nbr_lines_list_first_page)//nbr_lines_list):
    pdf.add_page()

for i in range(len(details)):
    if i%nbr_per_page == 0:
        pdf.add_page()
    details[i].append(puzzle_page(i, *details[i]))

pdf.page = 1
pdf.set_y(margins)
title_page(pack_title, details)

filename = ''
if args.output == '':
    filename, _ = f'{os.path.splitext(args.input)}.pdf'
else:
    filename = args.output
pdf.output(filename)