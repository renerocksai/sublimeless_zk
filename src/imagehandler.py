import re
import struct
import imghdr
import os


class ImageHandler:
    """
    Static class to bundle image handling.
    """
    ImgLinkMatcher = re.compile(r'(!\[)([^\n]*)(\]\()([^\n]*)(\))(\s*\{)?([^\}\n]*)(\})?')

    @staticmethod
    def show_images(editor, project, max_width=1024):
        """
        """
        folder = project.folder
        text = editor.text()
        editor.delete_all_images()
        for match in ImageHandler.ImgLinkMatcher.finditer(text):
            rel_p = match.group(4)
            if rel_p.startswith('http'):
                continue

            img = os.path.join(folder, rel_p)
            size  = ImageHandler.get_image_size(img)
            print('size for', rel_p, size)
            if not size:
                continue
            w, h = size
            imgattr = match.group(7)
            if not imgattr:
                if w > max_width:
                    m = max_width / w
                    h *= m
                    w = max_width
            size = (h,w)
            textposition = match.start()
            line, _ = editor.lineIndexFromPosition(textposition)
            editor.add_image(img, (10, line+1), (int(w/2), int(h/2)))

    @staticmethod
    def get_image_size(img):
        """
        Determine the image type of img and return its size.
        """
        with open(img, 'rb') as f:
            head = f.read(24)
            # print('head:\n', repr(head))
            if len(head) != 24:
                return
            if imghdr.what(img) == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return
                width, height = struct.unpack('>ii', head[16:24])
            elif imghdr.what(img) == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
            elif imghdr.what(img) == 'jpeg':
                try:
                    f.seek(0) # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf:
                        f.seek(size, 1)
                        byte = f.read(1)
                        while ord(byte) == 0xff:
                            byte = f.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', f.read(2))[0] - 2
                    # SOFn block
                    f.seek(1, 1)  # skip precision byte.
                    height, width = struct.unpack('>HH', f.read(4))
                except Exception:
                    return
            else:
                return
            return width, height
