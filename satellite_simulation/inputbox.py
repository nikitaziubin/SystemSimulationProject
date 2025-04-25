import pygame

pygame.init()
FONT = pygame.font.Font(None, 26)

class InputBox:
    def __init__(self, x, y, w, h, label_text='', default_text='', is_float=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = default_text
        self.txt_surface = FONT.render(self.text, True, pygame.Color('white'))
        self.active = False
        self.label = FONT.render(label_text, True, pygame.Color('white'))
        self.label_pos = (x, y - 25)
        self.is_float = is_float  # if True, allow dot for float input

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                self.color = self.color_inactive
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Accept numbers or dot if float input is enabled
                if len(self.text) < 10:
                    if event.unicode.isdigit():
                        self.text += event.unicode
                    elif self.is_float and event.unicode == '.' and '.' not in self.text:
                        self.text += '.'
            self.txt_surface = FONT.render(self.text, True, pygame.Color('white'))

    def draw(self, screen):
        screen.blit(self.label, self.label_pos)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_value(self):
        if self.text == '':
            return 0.0 if self.is_float else 0
        try:
            return float(self.text) if self.is_float else int(self.text)
        except ValueError:
            return 0.0 if self.is_float else 0
