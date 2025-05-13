import pygame

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.current_val = float(initial_val)
        self.label = label
        self.font = pygame.font.SysFont(None, 20)

        self.track_color = (100, 100, 100)
        self.knob_color = (200, 200, 200)
        self.knob_hover_color = (230, 230, 230)
        self.value_text_color = (255, 255, 255)

        self.knob_radius = height // 2 + 2
        self.knob_pos_x = 0
        self.update_knob_pos()

        self.dragging = False

    def update_knob_pos(self):
        """ Calculates the knob's center X based on the current value. """
        val_ratio = (self.current_val - self.min_val) / (self.max_val - self.min_val)
        self.knob_pos_x = self.rect.x + self.knob_radius + val_ratio * (self.rect.width - 2 * self.knob_radius)
        self.knob_pos_x = max(self.rect.x + self.knob_radius, min(self.knob_pos_x, self.rect.x + self.rect.width - self.knob_radius))


    def update_value_from_pos(self, mouse_x):
        """ Calculates the slider value based on the mouse X position. """
        track_start_x = self.rect.x + self.knob_radius
        track_width_actual = self.rect.width - 2 * self.knob_radius

        clamped_mouse_x = max(track_start_x, min(mouse_x, track_start_x + track_width_actual))

        val_ratio = (clamped_mouse_x - track_start_x) / track_width_actual
        self.current_val = self.min_val + val_ratio * (self.max_val - self.min_val)
        self.current_val = max(self.min_val, min(self.current_val, self.max_val))
        self.update_knob_pos()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                if abs(mouse_x - self.knob_pos_x) < self.knob_radius * 1.5 and self.rect.collidepoint(mouse_x, mouse_y):
                    self.dragging = True
                elif self.rect.collidepoint(mouse_x, mouse_y):
                     self.dragging = True
                     self.update_value_from_pos(mouse_x)


        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, _ = event.pos
                self.update_value_from_pos(mouse_x)

    def draw(self, surface):
        track_rect = self.rect.copy()
        track_rect.height = self.rect.height // 2
        track_rect.centery = self.rect.centery
        pygame.draw.rect(surface, self.track_color, track_rect, border_radius=track_rect.height // 2)

        knob_center = (int(self.knob_pos_x), self.rect.centery)
        current_knob_color = self.knob_color
        pygame.draw.circle(surface, current_knob_color, knob_center, self.knob_radius)

        value_text = f"{self.label}{self.current_val:.1f}x" # Show speed with 1 decimal place
        text_surface = self.font.render(value_text, True, self.value_text_color)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.y - 10))
        surface.blit(text_surface, text_rect)


    def get_value(self):
        return self.current_val

    def set_value(self, value):
        """ Allows setting the value programmatically """
        self.current_val = max(self.min_val, min(float(value), self.max_val))
        self.update_knob_pos()