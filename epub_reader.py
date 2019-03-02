import ebooklib
from ebooklib import epub
import os
from bs4 import BeautifulSoup
import copy
from PIL import Image, ImageDraw, ImageFont
import pylab
from tqdm import trange


EpubBookData = {
    'title': '',
    'cover': '',
    'contents': []
}


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.getText()
    res = ''
    for line in text.split('\n'):
        while line is not None and len(line) > 2 and (line[0] == ' ' or line[0] == '　'):
            line = line[1:]
        if line is not None and len(line) > 1 and line[0] != '\n':
            # print(line)
            res = res + line + '\n'
    return res


def do_it(filename):
    print("Filename:", filename)
    book = epub.read_epub(filename)
    data = copy.deepcopy(EpubBookData)
    print("book name:", book.get_metadata("DC", 'title'))
    data['title'] = book.get_metadata("DC", 'title')[0][0]
    print("book cover:", book.get_metadata("OPF", 'cover'))
    data['cover'] = book.get_metadata("OPF", 'cover')[0][1]['content']
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            res = parse_html(item.get_content())
            data['contents'].append({'title': (item.get_name().split('/')[-1]).split('.')[0], 'text': res})

    form_book(data)


PageData = {
    'lines': [],
    'chapter': '',
    'height': 0,
    'width': 0,
    'end_of_line': 1,
    'end_of_char': 0
}


def ups(x):
    if x >= 0:
        return x
    return 0


def calc_blanks(lines, width):
    blanks = 0
    for line in lines:
        blanks = blanks + ups(width - len(line))
    return blanks


def show_one_page(lines):
    # for line in lines:
    #     while line != '':
    #         print(line[:width])
    #         line = line[width:]
    for line in lines:
        print(line)


def get_one_page(lines, target_height, max_width):
    page_data = copy.deepcopy(PageData)
    if len(lines) <= 1:
        return page_data

    page_data['height'] = target_height
    width = max_width

    result = []
    flag = True
    offset = 0
    offset_char = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        offset_bk = offset
        if flag is False:
            break
        while line != '':
            result.append(line[:width])
            offset = offset + 1
            if len(result) == target_height:
                flag = False
                offset_char = (offset - offset_bk) * width
                break
            line = line[width:]
        i = i + 1

    page_data['lines'] = result
    page_data['width'] = width
    page_data['end_of_line'] = i - 1
    page_data['end_of_char'] = offset_char
    return page_data


def form_book(book_data, height=40, max_width=70):
    gblanks = []
    img_pages = []

    for chapter in book_data['contents']:
        print("Parsing:", chapter['title'])
        lines = chapter['text'].split('\n')
        start = 0
        offset_char = 0
        while start < len(lines):
            page_lines = lines[start:start+height]
            if len(page_lines) == 0:
                break
            page_lines[0] = page_lines[0][offset_char:]
            mblanks = []

            mwidth = 0
            for line in page_lines:
                if mwidth < len(lines):
                    mwidth = len(lines)

            if mwidth > max_width:
                mwidth = max_width

            for w in range(mwidth, 1, -1):
                page_data = get_one_page(page_lines, height, w)
                # print("real len of lines:", len(page_data['lines']))
                # print('end_of_line', page_data['end_of_line'], 'end_of_char:', page_data['end_of_char'])
                # show_one_page(page_data['lines'])

                # print('RAW:')
                # show_one_page(page_lines)
                blanks = calc_blanks(page_data['lines'], w)
                blanks = blanks - (mwidth - w) * height // 2
                mblanks.append(blanks)

            # print(len(mblanks), 'blanks:', mblanks)
            gblanks.append(mblanks)

            index = 0
            min_b = 99999999
            for b in range(len(mblanks)):
                if min_b > abs(mblanks[b]):
                    index = b
                    min_b = mblanks[b]
            # print('use abs:', mblanks[index], 'use width:', max_width - index - 1)
            page_data = get_one_page(page_lines, height, mwidth - index - 1)
            offset_char = page_data['end_of_char']
            start = start + page_data['end_of_line']

            # show_one_page(page_data['lines'])
            img_page = draw_one_page(page_data, book_data, progress=float(start/len(lines)), chapter=chapter['title'])
            if img_page is not None:
                img_pages.append(img_page)

    # gsum = [0, ] * (max_width - 3)
    # for b in gblanks:
    #     for x in range(len(b)):
    #         gsum[x] = gsum[x] + b[x]
    # for b in gblanks:
    #     pylab.plot(range(27), b)
    # pylab.plot(range(max_width - 3), gsum)
    # pylab.show()

    sumx = 0
    for i in img_pages:
        sumx = sumx + i.size[0]
    final = Image.new("RGB", (sumx, img_pages[0].size[1]))
    sumx = 0
    for i in trange(len(img_pages)):
        final.paste(img_pages[i], box=(sumx, 0))
        sumx = sumx + img_pages[i].size[0]
    final.show()
    final.save('%s.png' % book_data['title'])


font = ImageFont.truetype("msyh.ttc", 15)
font_small = ImageFont.truetype("msyh.ttc", 10)


def draw_one_text(page_data):
    if page_data['height'] == 0 or page_data['width'] == 0:
        return None
    img = Image.new("RGB", ((page_data['width'] + 1) * text_size[0], (page_data['height'] + 1) * text_size[1]),
                    color='white')
    d = ImageDraw.Draw(img)
    d.ink = 0   # Black
    for y in range(len(page_data['lines'])):
        line = page_data['lines'][y]
        d.multiline_text((0, y * text_size[1]), line, font=font)
    # print(img)
    # img.show()
    return img


def draw_one_page(page_data, book_data, progress=0.0, chapter=''):
    img_text = draw_one_text(page_data)
    if img_text is None:
        return
    img_page = Image.new("RGB", (img_text.size[0] + text_size[0] * 2, img_text.size[1] + text_size[1] * 2),
                         color='white')
    img_page.paste(img_text, box=(text_size[0], text_size[1]))
    draw = ImageDraw.Draw(img_page)
    draw.ink = 0
    draw.text((0, 2), book_data['title'], font=font_small)
    draw.text((0, img_page.size[1] - text_size_small[1] - 2), chapter, font=font_small)
    chapter_size = draw.textsize(chapter, font=font_small)
    draw.text((chapter_size[0] + text_size_small[0], img_page.size[1]-text_size_small[1]-2), "%.2f%%" % (progress * 100),
              font=font_small)
    draw.line((text_size[0], img_page.size[1]-text_size_small[1]-2-4,
               img_text.size[0] * progress, img_page.size[1]-text_size_small[1]-2-4))
    draw.line((img_page.size[0]-1, 0, img_page.size[0]-1, img_page.size[1]))
    # img_page.show()
    return img_page


if __name__ == '__main__':
    temp = Image.new("RGB", (512, 512))
    temp_draw = ImageDraw.Draw(temp)
    text_size = temp_draw.textsize('国', font=font)
    text_size_small = temp_draw.textsize('国', font=font_small)

    os.chdir('epub/')
    _li = os.listdir('.')
    for _i in _li:
        if _i[-5:] == '.epub':
            do_it(_i)

