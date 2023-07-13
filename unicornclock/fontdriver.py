
class FontDriver:

    variable_mode = True

    # Used if variable_mode = False
    char_width = 6

    chars_font_bounds = {}

    space_between_char = 1

    callback_text_write_char = None

    def __init__(self, galactic, graphics, font):
        self.galactic = galactic
        self.graphics = graphics
        self.font = font

        if self.variable_mode:
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
            if self.variable_mode:
                dims = self.chars_font_bounds[char]
                offset -= dims[0]

            yield (
                char,
                offset,
                dims[1] + 1 if self.variable_mode else self.char_width,
            )

            if self.variable_mode:
                offset += dims[1] + 1 + self.space_between_char
            else:
                offset += self.char_width + self.space_between_char

    def get_chars_bounds(self, text):
        yield from self.iter_chars(text)

    def write_char(self, char, x, y=0):
        char = str(char)

        try:
            self.font[str(char)]
        except KeyError:
            raise Exception("Character '%s' not found in font." % char)

        for (px, py) in self.iter_pixel(char):
            self.graphics.pixel(x + px, y + py)

    def write_text(self, text, x, y):
        for i, (char, offset, _) in enumerate(self.iter_chars(text)):
            if self.callback_text_write_char:
                self.callback_text_write_char(char, i)

            self.write_char(char, x + offset, y)
