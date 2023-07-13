from time import sleep


class CharacterSlideDownAnimation:
    """Character slide down animation"""

    async def update_time(self, time):
        if self.last_time is None:
            self.write_time(time)
            self.last_time = time

        _, HEIGHT = self.graphics.get_bounds()

        char = 0
        y = self.y
        for i in range(HEIGHT * 2 + 1):
            for index, offset, size, a, b in self.iter_on_changes(time):
                character = a if i <= HEIGHT else b

                self.graphics.set_clip(self.x + offset, 0, size, HEIGHT)
                self.graphics.set_pen(self.background_color)
                self.graphics.clear()

                self.callback_text_write_char(character, index)
                self.write_char(character, self.x + offset, y)

            self.galactic.update(self.graphics)

            y += 1
            if y >= HEIGHT:
                char += 1
                if char == 10:
                    char = 0
                y = -HEIGHT

            sleep(0.01)

        self.last_time = time
