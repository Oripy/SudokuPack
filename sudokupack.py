import os
import argparse
import re
parser = argparse.ArgumentParser()

parser.add_argument('input', type=argparse.FileType('r'), help='input filename')
parser.add_argument('output', nargs='?', help='pdf output filename - default to csv name')
parser.add_argument('--ppp', type=int, default=2, help='number of puzzle per page')
parser.add_argument('-n' '--numbering', default='auto', choices=['auto', 'none', 'custom'], help='define if puzzles should be numbered (auto), not numbered (none) or (custom). custom will take the fist value on each line of input file, replacing "_" as spaces.)')

args = parser.parse_args()

url_check = re.compile(r'(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})(\.[a-zA-Z0-9]{2,})?')

import fpdf
from fpdf.enums import XPos, YPos
from PIL import Image

pdf = fpdf.FPDF(orientation='P', format='A4', unit='mm')
pdf.add_page()

pdf.add_font('DejaVuSans', '', "DejaVuSans.ttf")
pdf.add_font('DejaVuSans', 'B', "DejaVuSans-Bold.ttf")
pdf.add_font('DejaVuSans', 'I', "DejaVuSans-Oblique.ttf")
pdf.add_font('Noto', '', 'NotoColorEmoji-Regular.ttf')

pdf.set_fallback_fonts(["Noto"], exact_match=False)

pdf.set_font("DejaVuSans", "B", 14)
margins = 15
puzzle_margin = 40
nbr_per_page = args.ppp
offset = 270/nbr_per_page
divider_height = 5
pdf.set_margins(margins, margins)
skipped = 0

column_width = 90
nbr_lines_list_first_page = 45
nbr_lines_list = 50

def title_page(title, intro, details):
    pdf.set_font("", "B", 30)
    for elem in title.split('\\n'):
        pdf.cell(0, h=10, text=elem, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("", "", 20)
    pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT, border="T")
    pdf.set_font("", "", 14)
    if intro != '':
        pdf.multi_cell(0, text=f'{intro}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT, border="T")
    for line in details:
        if line[7] == '':
            numbering = ''
        else:
            numbering = f'{line[7]} - '
        pdf.cell(0, h=5, text=f'{numbering}{line[2]}{f' by {line[3]}' if line[3] != "" else ""}\n', new_x=XPos.LMARGIN, new_y=YPos.NEXT, link=line[8])

def puzzle_page(nbr, links, real_url, title, author, rules, image, source, numbering):
    global skipped
    position = (nbr + skipped)%nbr_per_page
    pdf.set_font("", "", 12)
    pdf.set_y(position*offset+puzzle_margin)

    with pdf.offset_rendering() as dummy:
        # Dummy rendering to check if page break is needed
        dummy.multi_cell(column_width, None, f'{rules}\n{source}')

    if dummy.page_break_triggered:
        pdf.add_page()
        skipped += 1
        position = (nbr + skipped)%nbr_per_page

    pdf.set_y(position*(offset-divider_height)+margins)
    if position != 0:
        pdf.cell(0, h=divider_height, new_x=XPos.LMARGIN, new_y=YPos.NEXT, border="T")
    pdf.image(image, margins, position*offset+puzzle_margin, column_width, link=real_url)
    pdf.set_font("", "B", 20)
    anchor = pdf.add_link()
    pdf.set_link(anchor, position*offset+margins)
    if numbering == '':
        pdf.write(text=f'{title}\n')
    else:
        pdf.write(text=f'{numbering} - {title}\n')
    if author != "":
        pdf.set_font("", "I", 20)
        pdf.write(text=f'by {author}\n')
    pdf.set_font("", "", 14)
    pdf.write(text=links[0], link=real_url)
    pdf.set_font("", "", 12)
    for link in links[1:]:
        pdf.write(text=f'\nAlt link: {link}', link=link)
    pdf.set_font("", "", 12)
    pdf.set_y(position*offset+puzzle_margin)
    pdf.set_x(-(margins + column_width))
    pdf.multi_cell(column_width, None, rules)
    if source != "":
        pdf.set_x(-(margins + column_width))
        pdf.set_font("", "I", 10)
        pdf.write(text="source", link=source)
    next_position = (nbr + skipped + 1)%nbr_per_page
    if next_position != 0:
        next_y = next_position*(offset-divider_height)+margins
        if pdf.get_y() > next_y:
            skipped += 1
    return anchor

from puzzle_url_tools import get_image_and_rules

lines = args.input.read().splitlines()
pack_title = ''
pack_intro = ''
details = []
for line in lines:
    if line == '':
        continue
    print(line)
    urls = []
    author_given = ""
    rules_given = ""
    splited_line = line.split()
    match args.n__numbering:
        case 'custom':
            numbering = splited_line[0].replace('_', ' ')
        case 'auto':
            numbering = len(details) + 1
        case _:
            numbering = ''
    for i in range(len(splited_line)):
        if args.n__numbering == 'custom' and i == 0:
            continue
        if url_check.match(splited_line[i]):
            urls.append(splited_line[i])
        else:
            author_given = splited_line[i]
            break
    if len(splited_line) > (len(urls) + (1 if author_given != "" else 0)):
        rules_given = " ".join(line.split()[(len(urls) + (1 if author_given != "" else 0) + (1 if args.n__numbering == 'custom' else 0)):])

    if len(urls) == 0:
        if pack_title == '':
            pack_title = line
        else:
            pack_intro += line + '\n'
        continue
    real_url, title, author, rules, img, source = get_image_and_rules(urls[0])
    if author == "":
        author = author_given
    if rules == "":
        rules = rules_given
    details.append([urls, real_url, title, author, rules, img, source, numbering])

# Allow more pages for title page if it will overflow
if len(details) > nbr_lines_list_first_page:
    pdf.add_page()
for i in range((len(details)-nbr_lines_list_first_page)//nbr_lines_list):
    pdf.add_page()

for i in range(len(details)):
    if (i + skipped)%nbr_per_page == 0:
        pdf.add_page()
    details[i].append(puzzle_page(i, *details[i]))

pdf.page = 1
pdf.set_y(margins)
title_page(pack_title, pack_intro, details)

filename = ''
if args.output == '':
    filename, _ = f'{os.path.splitext(args.input)}.pdf'
else:
    filename = args.output
pdf.output(filename)
