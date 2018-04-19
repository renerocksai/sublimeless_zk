
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *

from textshortcuts import EditorTextShortCutHandler


class ZettelkastenScintilla(QsciScintilla):
    """
    Specialized QScintilla editor that allows insertion and deletion
    of images into the editor itself.
    """


    class Image:
        """
        Class for holding an image's information
        """

        def __init__(self, image, position, size=None):
            if isinstance(image, str) == False:
                raise Exception("Enter path to image as a string.")
            elif isinstance(position, tuple) == False or len(position) != 2:
                raise Exception("Image position should be of type tuple(int, int)!")
            elif size != None and (isinstance(position, tuple) == False \
                                           or len(position) != 2):
                raise Exception("Image size has to be of type tuple(int, int)!")
            # Assign the properties
            self.image = QImage(image)
            if size != None:
                self.image = self.image.scaled(*size)
            self.position = position
            self.size = size
    ''''''

    maximum_image_count = 100
    image_list = None
    calculation_font = None
    line_list = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_list = {}
        self.line_list = []
        # Connect the special SCN_MODIFIED signal, that gives details of
        # changes in the editor's text.
        self.SCN_MODIFIED.connect(self.text_changed)

        self.text_shortcut_handler = EditorTextShortCutHandler(self)
    ''''''

    def set_calculation_font(self, font):
        """
        Set the font for calculating the font metrics like font width and height
        Parameters:
            font -> QFont, a QFont that will be used for the calculations
        """
        if isinstance(font, QFont) == False:
            raise Exception("The calculation font has to be a QFont!")
        self.calculation_font = font
    ''''''

    def add_image(self, image, position, size):
        """
        Add the image to the image list.
        Parameters:
            image -> str, path to image
            position -> tuple(int, int), the COLUMN and LINE offset for the image position
            size -> tuple(int, int), the height and width of the displayed image.
                    If None, the original image size will be used.
        Return value:
            index -> int, index of the added image
        """
        image = self.Image(image, position, size)
        for i in range(self.maximum_image_count):
            if not (i in self.image_list.keys()):
                self.image_list[i] = image
                return i
        else:
            raise Exception("Too many images in the editor, the maximum is '{}'"\
                            .format(self.maximum_image_count))
    ''''''

    def delete_image(self, index):
        """
        Delete an image from the image list using it's index number
        Parameters:
            index -> int, the index of the image
        """
        if isinstance(index, int) == False or index > self.maximum_image_count:
            raise Exception(
                "Index for deletion should be smaller integer than maximum_image_count")
        # Delete the image from the image list by
        # poping the entry out of the dictionary!
        self.image_list.pop(index, None)
    ''''''

    def get_font_metrics(self, font):
        font_metrics = QFontMetrics(font)
        single_character_width = font_metrics.width("A")  # Works for monospaced fonts!
        # For other fonts it is a good enough estimate.
        single_character_height = font_metrics.height()
        return single_character_width, single_character_height
    ''''''

    def text_changed(self,
                     position,
                     mod_type,
                     text,
                     length,
                     lines_added,
                     line,
                     fold_level_now,
                     fold_level_prev,
                     token,
                     additional_lines_added):
        """
        This is a function connected to the SCN_MODIFIED signal.
        It gives great information of what changes happened in the editor.
        """
        insert_flag = mod_type & 0b1
        delete_flag = mod_type & 0b10
        if insert_flag or delete_flag:
            change_line, change_column = self.lineIndexFromPosition(position)
            #            print(change_line, lines_added)
            if lines_added != 0:
                # Loop through the lines and adjust the Y(LINE) position offset
                for key, image in self.image_list.items():
                    x, y = image.position
                    if y >= change_line:
                        image.position = (x, y + lines_added)
    ''''''

    def paintEvent(self, e):
        super().paintEvent(e)
        # Get the painting frame details
        current_parent_size = self.size()
        first_visible_line = self.SendScintilla(self.SCI_GETFIRSTVISIBLELINE)
        column_offset_in_pixels = self.SendScintilla(self.SCI_GETXOFFSET)
        single_character_width, single_character_height = self.get_font_metrics(
            self.calculation_font
        )
        # Initialize the painter
        painter = QPainter()
        painter.begin(self.viewport())
        # Loop throught the images and paint them
        for i in self.image_list.keys():
            # Set the paint offsets
            image = self.image_list[i].image
            paint_offset_x = (self.image_list[i].position[0] * single_character_width)\
                             - column_offset_in_pixels
            paint_offset_y = (self.image_list[i].position[1] - first_visible_line)\
                             * single_character_height
            # Paint the image
            painter.drawImage(QPoint(paint_offset_x, paint_offset_y), image)
        # Close the painter
        painter.end()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.text_shortcut_handler.keyPressEvent(event)

    ''''''
