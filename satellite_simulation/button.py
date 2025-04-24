import pygame
button_font = pygame.font.SysFont(None, 24)

class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.color = (200, 200, 200)
        self.hover_color = (230, 230, 230)
        self.text_color = (0, 0, 0)

    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered() else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=5)
        text_surface = button_font.render(self.text, True, self.text_color)
        surface.blit(text_surface, (self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
                                     self.rect.y + (self.rect.height - text_surface.get_height()) // 2))

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def handle_click(self):
        if self.is_hovered():
            self.action()