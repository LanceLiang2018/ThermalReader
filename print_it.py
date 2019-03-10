from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtCore import *
from PyQt5 import sip
import sys
import numpy as np

from PIL import Image
import os


class ImagePrinterWindow(QMainWindow):
    def __init__(self, parent=None, image=None, paper_type='58'):
        super(ImagePrinterWindow, self).__init__(parent)

        printer = QPrinter()
        # printer.setOutputFormat(QPrinter.PdfFormat)
        # printer.setOutputFileName("pdf.pdf")

        option = QTextOption(Qt.AlignLeft)
        option.setWrapMode(QTextOption.WordWrap)

        painter = QPainter()
        printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.begin(printer)
        if image is not None:
            # image = QImage(image)
            # image = Image.open(image)
            if image.size[1] < image.size[0]:
                image = image.rotate(270, expand=True)
            if paper_type == 'A4':
                width = printer.logicalDpiX() * (210 / 25.4)
                height = printer.logicalDpiY() * (297 / 25.4)
                if width / height < image.size[0] / image.size[1]:
                    rect = QRectF(0, 0, width, image.size[1] * (width / image.size[0]))
                else:
                    rect = QRectF(0, 0, image.size[0] * (height / image.size[1]), height)
            else:
                width = 180
                rect = QRectF(0, 0, width, image.size[1] * (width / image.size[0]))
            img = np.array(image)
            im = QImage(img[:], img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
            painter.drawImage(rect, im)
        painter.end()


app = QApplication(sys.argv)

Image.MAX_IMAGE_PIXELS = 1000000000

os.chdir('./epub/')
li = os.listdir('.')
image_paths = []
for i in li:
    if i[-6:] == '_pages':
        image_paths.append(i)

for image_file in image_paths:
    imgs = os.listdir("%s/res" % image_file)
    imgs.sort()
    print(imgs)
    input()

    for im in imgs:
        print("Print:", "%s/res/%s" % (image_file, im))
        image = Image.open("%s/res/%s" % (image_file, im)).convert('RGB')
        # printer.print_image(image=image)
        window = ImagePrinterWindow(image=image)
        app.closeAllWindows()
        input()
