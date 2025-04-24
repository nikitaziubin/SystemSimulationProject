import pygame

pygame.init()
FONT = pygame.font.Font(None, 26)

class InputBox:
    def __init__(self, x, y, w, h, label_text='', default_text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = default_text
        self.txt_surface = FONT.render(self.text, True, self.color)
        self.active = False
        self.label = FONT.render(label_text, True, pygame.Color('white'))
        self.label_pos = (x, y - 25)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active if clicked inside box
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.color = self.color_inactive
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < 10 and event.unicode.isdigit():
                        self.text += event.unicode
                self.txt_surface = FONT.render(self.text, True, pygame.Color('white'))

    def draw(self, screen):
        # Draw label and input box
        screen.blit(self.label, self.label_pos)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_value(self):
        return int(self.text) if self.text.isdigit() else 0
