import ebooklib
from ebooklib import epub
import os
from bs4 import BeautifulSoup
import copy
from PIL import Image, ImageDraw, ImageFont
import pylab
from tqdm import trange
from io import BytesIO


EpubBookData = {
    'title': '',
    'cover': '',
    # 'images': [],
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
    global page_count
    page_count = 1
    print("Filename:", filename)
    book = epub.read_epub(filename)
    data = copy.deepcopy(EpubBookData)
    print("book name:", book.get_metadata("DC", 'title'))
    data['title'] = book.get_metadata("DC", 'title')[0][0]
    print("book cover:", book.get_metadata("OPF", 'cover'))
    if len(book.get_metadata("OPF", 'cover')) > 0:
        data['cover'] = book.get_metadata("OPF", 'cover')[0][1]['content']
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            res = parse_html(item.get_content())
            data['contents'].append({'title': (item.get_name().split('/')[-1]).split('.')[0], 'text': res})
        if item.get_type() == ebooklib.ITEM_IMAGE:
            img_data = BytesIO(item.get_content())
            img = Image.open(img_data).convert("L")
            # data['images'].append(img)
            data['contents'].append({'title': (item.get_name().split('/')[-1]).split('.')[0], 'image': img})

    form_book_const(data)


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


def blend_image(dist, src):
    new = Image.new("L", (dist.size[0] + src.size[0], dist.size[1]))
    new.paste(dist, (0, 0))
    new.paste(src, (dist.size[0], 0))
    return new


def form_book(book_data, height=15, max_width=40):
    gblanks = []
    img_pages = []

    result = Image.new("L", (1, (height + 1) * text_size[1] + 2 * text_size_small[1]))

    for image in book_data['images']:
        img_height = (height + 1) * text_size[1] + 2 * text_size_small[1]
        image = image.resize((int(img_height / image.size[1] * image.size[0]), img_height))
        # img_pages.append(image)
        result = blend_image(result, image)

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
            min_width = 10
            if min_width > mwidth:
                min_width = mwidth

            for w in range(mwidth, min_width, -1):
                page_data = get_one_page(page_lines, height, w)
                # print("real len of lines:", len(page_data['lines']))
                # print('end_of_line', page_data['end_of_line'], 'end_of_char:', page_data['end_of_char'])
                # show_one_page(page_data['lines'])

                # print('RAW:')
                # show_one_page(page_lines)
                blanks = calc_blanks(page_data['lines'], w)
                blanks = blanks - (mwidth - w) * height // 1
                mblanks.append(blanks)

            # print(len(mblanks), 'blanks:', mblanks)
            gblanks.append(mblanks)

            index = 0
            min_b = 99999999
            for b in range(len(mblanks)):
                if min_b > abs(mblanks[b]):
                    index = b
                    min_b = mblanks[b]

            # hard_width = 30
            # if hard_width > mwidth:
            #     hard_width = mwidth

            # print('use abs:', mblanks[index], 'use width:', max_width - index - 1)
            page_data = get_one_page(page_lines, height, mwidth - index - 1)
            # page_data = get_one_page(page_lines, height, hard_width)
            offset_char = offset_char + page_data['end_of_char']
            start = start + page_data['end_of_line']

            # show_one_page(page_data['lines'])
            img_page = draw_one_page(page_data, book_data, progress=float(start/len(lines)), chapter=chapter['title'])
            if img_page is not None:
                # img_pages.append(img_page)
                result = blend_image(result, img_page)

    # gsum = [0, ] * (max_width - 3)
    # for b in gblanks:
    #     for x in range(len(b)):
    #         gsum[x] = gsum[x] + b[x]
    # for b in gblanks:
    #     pylab.plot(range(27), b)
    # pylab.plot(range(max_width - 3), gsum)
    # pylab.show()

    # sumx = 0
    # for i in img_pages:
    #     sumx = sumx + i.size[0]
    # final = Image.new("RGB", (sumx, img_pages[0].size[1]))
    # sumx = 0
    # for i in trange(len(img_pages)):
    #     final.paste(img_pages[i], box=(sumx, 0))
    #     sumx = sumx + img_pages[i].size[0]
    # final.show()
    # final.save('%s.png' % book_data['title'])
    if not os.path.exists('./%s_crops/' % book_data['title']):
        os.mkdir('%s_crops/' % book_data['title'])
    step = result.size[0] // 180
    for x in range(0, result.size[0], step):
        crop = result.crop((x, 0, x+step, result.size[1]))
        crop.save('%s_crops/%015d.jpg' % (book_data['title'], x))
    # result.save('%s.png' % book_data['title'])


page_count = 1


def save_one_page(page_title, page):
    global page_count
    filename = "%06d.jpg" % page_count
    path = "%s_pages" % page_title
    if not os.path.exists(path):
        os.mkdir(path)
    page.save("%s/%s" % (path, filename))
    page_count = page_count + 1


def form_book_const(book_data, height=15, width=20):
    img_height = (height + 1) * text_size[1] + 2 * text_size_small[1]
    for chapter in book_data['contents']:
        if 'image' in chapter:
            print("Parsing Image:", chapter['title'])
            image = chapter['image']
            image = image.resize((int(img_height / image.size[1] * image.size[0]), img_height))
            # img_pages.append(image)
            # result = blend_image(result, image)
            save_one_page(book_data['title'], image)
            continue
        print("Parsing Text:", chapter['title'])
        lines = chapter['text'].split('\n')
        start = 0
        offset_char = 0
        while start < len(lines):
            page_lines = lines[start:start+height]
            if len(page_lines) == 0:
                break
            page_lines[0] = page_lines[0][offset_char:]

            page_data = get_one_page(page_lines, height, width)
            if page_data['end_of_line'] > 0:
                offset_char = 0
            offset_char = offset_char + page_data['end_of_char']
            start = start + page_data['end_of_line']

            # print('=' * width * 2)
            # print('Got eline:', page_data['end_of_line'], 'echar:', page_data['end_of_char'],
            #       'start:', start, 'offset:', offset_char)
            # for pline in page_data['lines']:
            #     print(pline)

            # show_one_page(page_data['lines'])
            img_page = draw_one_page(page_data, book_data, progress=float(start/len(lines)), chapter=chapter['title'])
            if img_page is not None:
                # img_pages.append(img_page)
                # result = blend_image(result, img_page)
                save_one_page(book_data['title'], img_page)

    pages_path = "%s_pages" % book_data['title']
    pages = os.listdir(pages_path)
    last_img_origin = Image.new("L", (3, img_height), color='black')
    last_img = last_img_origin.copy()
    path = "%s_pages/res" % book_data['title']
    if not os.path.exists(path):
        os.mkdir(path)
    res_count = 1
    # for page_file in pages:
    for i in trange(len(pages)):
        page_file = pages[i]
        if page_file[-4:] != '.jpg':
            continue
        if last_img.size[0] / last_img.size[1] > MAX_SPLIT:
            last_img.save("%s/%06d.jpg" % (path, res_count))
            res_count = res_count + 1
            last_img = last_img_origin.copy()
        image = Image.open("%s/%s" % (pages_path, page_file))
        last_img = blend_image(last_img, image)

    last_img.save("%s/%06d.jpg" % (path, res_count))
    res_count = res_count + 1


MAX_SPLIT = 320 / 58
font = ImageFont.truetype("msyh.ttc", 50)
font_small = ImageFont.truetype("msyh.ttc", 35)


def draw_one_text(page_data):
    if page_data['height'] == 0 or page_data['width'] == 0:
        return None
    img = Image.new("L", ((page_data['width'] + 1) * text_size[0], (page_data['height'] + 1) * text_size[1]),
                    color='white')
    d = ImageDraw.Draw(img)
    d.ink = 0   # Black
    for y in range(len(page_data['lines'])):
        line = page_data['lines'][y]
        d.multiline_text((0, y * text_size[1]), line, font=font)
    # print(img)
    # img.show()
    # print("Draw text:")
    # for line in page_data['lines']:
    #     print(line)
    return img


def draw_one_page(page_data, book_data, progress=0.0, chapter=''):
    img_text = draw_one_text(page_data)
    if img_text is None:
        return
    img_page = Image.new("L", (img_text.size[0] + text_size_small[0] * 1, img_text.size[1] + text_size_small[1] * 2),
                         color='white')
    img_page.paste(img_text, box=(text_size_small[0], text_size_small[1]))
    draw = ImageDraw.Draw(img_page)
    draw.ink = 0
    draw.text((0, 2), book_data['title'], font=font_small)
    draw.text((text_size_small[0], img_page.size[1] - text_size_small[1] - 2), chapter, font=font_small)
    chapter_size = draw.textsize(chapter, font=font_small)
    draw.text((chapter_size[0] + text_size_small[0], img_page.size[1]-text_size_small[1]-2), "  %.2f%%" % (progress * 100),
              font=font_small)
    draw.line((text_size[0], img_page.size[1]-text_size_small[1]-2-4,
               img_text.size[0] * progress, img_page.size[1]-text_size_small[1]-2-4), width=4)
    draw.line((0, 0, 0, img_page.size[1]), width=4)
    draw.line((img_page.size[0] - 1, 0, img_page.size[0] - 1, img_page.size[1]), width=4)
    # img_page.show()
    return img_page


if __name__ == '__main__':
    Image.MAX_IMAGE_PIXELS = 1000000000
    temp = Image.new("L", (512, 512))
    temp_draw = ImageDraw.Draw(temp)
    text_size = temp_draw.textsize('国', font=font)
    text_size_small = temp_draw.textsize('国', font=font_small)

    os.chdir('epub/')
    _li = os.listdir('.')
    for _i in _li:
        if _i[-5:] == '.epub':
            do_it(_i)

