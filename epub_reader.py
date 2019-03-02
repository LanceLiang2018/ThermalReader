import ebooklib
from ebooklib import epub
import os
from bs4 import BeautifulSoup
import copy
from PIL import Image


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
    data['title'] = book.get_metadata("DC", 'title')
    print("book cover:", book.get_metadata("OPF", 'cover'))
    data['cover'] = book.get_metadata("OPF", 'cover')
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            res = parse_html(item.get_content())
            data['contents'].append({'title': item.get_name(), 'text': res})

    form_book(data)


PageData = {
    'lines': [],
    'height': 0,
    'width': 0
}


def show_one_page(lines, width):
    for line in lines:
        while line != '':
            print(line[:width])
            line = line[width:]


def get_one_page(lines, target_height, max_width):
    page_data = copy.deepcopy(PageData)
    page_data['height'] = target_height
    width = max_width

    return page_data


def form_book(bookdata):
    for chapter in bookdata['contents']:
        lines = chapter['text'].split('\n')
        page_data = get_one_page(lines, 20, 20)
        show_one_page(lines, 30)


if __name__ == '__main__':
    os.chdir('epub/')
    li = os.listdir('.')
    for i in li:
        if i[-5:] == '.epub':
            do_it(i)
            # parse_html(i, 'text/part0006.html')

