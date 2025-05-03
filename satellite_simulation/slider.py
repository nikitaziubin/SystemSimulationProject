# slider.py
import pygame

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.current_val = float(initial_val)
        self.label = label
        self.font = pygame.font.SysFont(None, 20) # Font for label and value

        self.track_color = (100, 100, 100)
        self.knob_color = (200, 200, 200)
        self.knob_hover_color = (230, 230, 230)
        self.value_text_color = (255, 255, 255)

        self.knob_radius = height // 2 + 2 # Make knob slightly larger than track height
        self.knob_pos_x = 0 # Calculated in update_knob_pos
        self.update_knob_pos() # Set initial knob position

        self.dragging = False

    def update_knob_pos(self):
        """ Calculates the knob's center X based on the current value. """
        val_ratio = (self.current_val - self.min_val) / (self.max_val - self.min_val)
        self.knob_pos_x = self.rect.x + self.knob_radius + val_ratio * (self.rect.width - 2 * self.knob_radius)
        # Clamp knob position within track bounds
        self.knob_pos_x = max(self.rect.x + self.knob_radius, min(self.knob_pos_x, self.rect.x + self.rect.width - self.knob_radius))


    def update_value_from_pos(self, mouse_x):
        """ Calculates the slider value based on the mouse X position. """
        track_start_x = self.rect.x + self.knob_radius
        track_width_actual = self.rect.width - 2 * self.knob_radius

        # Clamp mouse_x to the drawable track area
        clamped_mouse_x = max(track_start_x, min(mouse_x, track_start_x + track_width_actual))

        val_ratio = (clamped_mouse_x - track_start_x) / track_width_actual
        self.current_val = self.min_val + val_ratio * (self.max_val - self.min_val)
        # Ensure value stays precisely within bounds due to float math
        self.current_val = max(self.min_val, min(self.current_val, self.max_val))
        self.update_knob_pos() # Update knob position based on new value

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mouse_x, mouse_y = event.pos
                # Check if click is on the knob (approximate check using knob radius)
                if abs(mouse_x - self.knob_pos_x) < self.knob_radius * 1.5 and self.rect.collidepoint(mouse_x, mouse_y):
                    self.dragging = True
                # Check if click is on the track (allow jumping to position)
                elif self.rect.collidepoint(mouse_x, mouse_y):
                     self.dragging = True
                     self.update_value_from_pos(mouse_x) # Jump to click position
                     # Optional: Call an action immediately on click?
                     # if hasattr(self, 'action') and callable(self.action): self.action(self.current_val)


        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, _ = event.pos
                self.update_value_from_pos(mouse_x)
                # Optional: Call an action continuously while dragging?
                # if hasattr(self, 'action') and callable(self.action): self.action(self.current_val)


    def draw(self, surface):
        # Draw track
        track_rect = self.rect.copy()
        track_rect.height = self.rect.height // 2 # Make track thinner than overall height
        track_rect.centery = self.rect.centery
        pygame.draw.rect(surface, self.track_color, track_rect, border_radius=track_rect.height // 2)

        # Draw Knob
        knob_center = (int(self.knob_pos_x), self.rect.centery)
        current_knob_color = self.knob_color
        # Optional: Highlight knob on hover (needs mouse pos check)
        # mouse_pos = pygame.mouse.get_pos()
        # if math.dist(mouse_pos, knob_center) < self.knob_radius:
        #     current_knob_color = self.knob_hover_color

        pygame.draw.circle(surface, current_knob_color, knob_center, self.knob_radius)

        # Draw Label and Value Text
        value_text = f"{self.label}{self.current_val:.1f}x" # Show speed with 1 decimal place
        text_surface = self.font.render(value_text, True, self.value_text_color)
        # Position text above the slider
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.y - 10))
        surface.blit(text_surface, text_rect)


    def get_value(self):
        return self.current_val

    def set_value(self, value):
        """ Allows setting the value programmatically """
        self.current_val = max(self.min_val, min(float(value), self.max_val))
        self.update_knob_pos()