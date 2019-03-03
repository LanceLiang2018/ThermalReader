from chat2_sdk import *
from PIL import Image
import os

os.chdir('./epub/')
li = os.listdir('.')
image_paths = []
for i in li:
    if i[-4:] == '.png':
        image_paths.append(i)

for image_file in image_paths:
    Image.MAX_IMAGE_PIXELS = 1000000000
    image = Image.open(image_file)
    printer = Chat2Printer()
    printer.print_image(image=image, paper_type='58')
    input()
