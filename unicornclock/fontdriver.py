
class FontDriver:

    chars_font_bounds = {}

    space_between_char = 1

    callback_write_char = None

    def __init__(self, galactic, graphics, font):
        self.galactic = galactic
        self.graphics = graphics
        self.font = font

        self.load_chars_font_bounds()

    def iter_pixel(self, char):
        """Iter pixel
        Yield only lighted pixel
        """
        for y, c in enumerate(self.font[char]):
            for bit in range(8):
                if c & (1 << bit):
                    yield (bit, y)

    def load_chars_font_bounds(self):
        self.chars_font_bounds = {}
        for char in self.font:
            min_x = 1000
            max_x = 0
            for (pos_x, pos_y) in self.iter_pixel(char):
                min_x = min(min_x, pos_x)
                max_x = max(max_x, pos_x)
            self.chars_font_bounds[char] = (min_x, max_x)

    def iter_chars(self, text):
        offset = 0
        for i, char in enumerate(text):
            dims = self.chars_font_bounds[char]

            # The `+1` is because we come from position to have a width
            character_width = dims[1] - dims[0] + 1

            yield (char, offset, character_width)

            space_between_char = self.space_between_char(i, char) \
                if callable(self.space_between_char) \
                    else self.space_between_char

            offset += character_width + space_between_char

    def get_chars_bounds(self, text):
        yield from self.iter_chars(text)

    def write_char(self, char, x, y=0):
        char = str(char)

        try:
            self.font[str(char)]
        except KeyError:
            raise Exception("Character '%s' not found in font." % char)

        start, _ = self.chars_font_bounds[char]
        for (px, py) in self.iter_pixel(char):
            self.graphics.pixel(x + px - start, y + py)

    def write_text(self, text, x, y):
        for i, (char, offset, _) in enumerate(self.iter_chars(text)):
            if self.callback_write_char:
                self.callback_write_char(char, i)

            self.write_char(char, x + offset, y)
