from time import sleep


class CharacterSlideAnimation:
    """Character slide animation"""

    # True: Down, False: Up
    direction = 1

    async def update_time(self, time):
        if self.last_time is None:
            self.write_time(time)
            self.last_time = time

        _, HEIGHT = self.graphics.get_bounds()

        if self.direction:
            y = self.y
        else:
            y = self.y + HEIGHT + 1

        for i in range(
            (HEIGHT * 2 if self.direction else HEIGHT + 1) + 1
        ):
            for index, offset, size, a, b in self.iter_on_changes(time):
                character = a if i <= HEIGHT else b

                self.graphics.set_clip(self.x + offset, 0, size, HEIGHT)
                self.graphics.set_pen(self.background_color)
                self.graphics.clear()

                self.callback_text_write_char(character, index)
                self.write_char(character, self.x + offset, y)

            self.galactic.update(self.graphics)

            if self.direction:
                y += 1
                if y >= HEIGHT:
                    y = -HEIGHT
            else:
                y -= 1

            sleep(0.01)

        self.last_time = time


class CharacterSlideDownAnimation(CharacterSlideAnimation):
    direction = True


class CharacterSlideUpAnimation(CharacterSlideAnimation):
    direction = False
