import pygame
import math
import random
import os # To help locate the image file

# Initialize Pygame
pygame.init()

# --- Configuration ---
WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Satellite Simulation v3") # Updated caption
clock = pygame.time.Clock()

# Colors
# ... (Colors remain the same) ...
BLACK = (0, 0, 0)
DARK_SPACE = (10, 10, 30)
SATELLITE_BLUE = (0, 0, 255)
SATELLITE_GREEN = (0, 255, 0)
BLINK_RED = (255, 50, 50)
DAMAGED_SATELLITE_COLOR = (100, 100, 100)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
STAR_COLOR = (200, 200, 200)
STATION_COLOR = (192, 192, 192)
STATION_SELECTED_COLOR = (255, 255, 255)
COMM_RADIUS_COLOR = (0, 80, 0)
COMM_RADIUS_SELECTED_COLOR = (0, 150, 0)
COMM_LINE_COLOR = (180, 180, 180)


# --- Constants ---
EARTH_RADIUS = 50
EARTH_POSITION = (WIDTH // 2, HEIGHT // 2)
STATION_MIN_DISTANCE = 40
MIN_STATION_COMM_RADIUS = 20
MAX_STATION_COMM_RADIUS = 400
STATION_SELECTION_RADIUS = 20
STATION_ALPHA_NORMAL = 100
STATION_ALPHA_SELECTED = 255
# *** Radius change amount per click ***
STATION_RADIUS_CLICK_CHANGE = 10

# Satellite Orbit Radii
MIN_ORBIT_RADIUS = EARTH_RADIUS + 30
MAX_ORBIT_RADIUS = min(WIDTH // 2, HEIGHT // 2) - 50

# Satellite Speeds
MIN_SPEED_A = 0.001
MAX_SPEED_A = 0.006
MIN_SPEED_B = 0.002
MAX_SPEED_B = 0.004

# Damage & Blinking
SATELLITE_DAMAGE_PROBABILITY = 0.0003
BLINK_DURATION_MS = 5000
BLINK_INTERVAL_MS = 250

# Star Background
STAR_COUNT = 350
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1.5)) for _ in range(STAR_COUNT)]

# Font
font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 22)
button_font = pygame.font.SysFont(None, 24)

# --- Load Assets ---
earth_image = None
try:
    earth_image_path = 'earth_texture.png' # <<< ENSURE YOU HAVE THIS IMAGE FILE >>>
    if os.path.exists(earth_image_path):
        earth_image_original = pygame.image.load(earth_image_path).convert_alpha()
        earth_image = pygame.transform.scale(earth_image_original, (EARTH_RADIUS * 2, EARTH_RADIUS * 2))
    else:
        print(f"Warning: Earth image '{earth_image_path}' not found. Drawing blue circle instead.")
except pygame.error as e:
    print(f"Error loading Earth image: {e}. Drawing blue circle instead.")

# --- Global Variables ---
selected_station = None

# --- Classes ---

class Satellite:
    # ... (Satellite class remains the same) ...
    def __init__(self, orbit_radius, speed, color):
        self.orbit_radius = orbit_radius
        self.speed = speed
        self.initial_color = color
        self.color = color
        self.angle = random.uniform(0, 2 * math.pi)
        self.status = 'operational' # 'operational', 'damaging', 'destroyed'
        self.x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
        self.y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)
        # Blinking state
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_on = False # Current visual state of blink

    def update(self, current_ticks):
        if self.status == 'operational':
            # Movement
            self.angle += self.speed
            self.angle %= 2 * math.pi
            self.x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
            self.y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)

            # Damage Check
            if random.random() < SATELLITE_DAMAGE_PROBABILITY:
                self.status = 'damaging'
                self.is_blinking = True
                self.blink_start_time = current_ticks
                # print(f"Satellite at radius {self.orbit_radius:.0f} started damaging!") # Optional print

        elif self.status == 'damaging':
            elapsed_blink_time = current_ticks - self.blink_start_time
            if elapsed_blink_time > BLINK_DURATION_MS:
                self.status = 'destroyed'
                self.is_blinking = False
                # print(f"Satellite at radius {self.orbit_radius:.0f} destroyed.") # Optional print
            else:
                # Update blinking state
                self.blink_on = (elapsed_blink_time // BLINK_INTERVAL_MS) % 2 == 0
                self.color = BLINK_RED if self.blink_on else DAMAGED_SATELLITE_COLOR

    def draw(self, surface):
        if self.status == 'destroyed':
            return

        x, y = self.x, self.y
        body_radius = 6
        panel_length = 15
        panel_width = 3

        pygame.draw.circle(surface, self.color, (int(x), int(y)), body_radius)

        if self.status == 'operational' or self.blink_on:
            panel_color = (200, 200, 0)
        else:
             panel_color = (80, 80, 80)

        panel_angle_rad = self.angle + math.pi / 2
        p1_x = x + math.cos(panel_angle_rad) * (body_radius + panel_length)
        p1_y = y + math.sin(panel_angle_rad) * (body_radius + panel_length)
        p2_x = x - math.cos(panel_angle_rad) * (body_radius + panel_length)
        p2_y = y - math.sin(panel_angle_rad) * (body_radius + panel_length)

        pygame.draw.line(surface, panel_color, (int(x), int(y)), (int(p1_x), int(p1_y)), panel_width)
        pygame.draw.line(surface, panel_color, (int(x), int(y)), (int(p2_x), int(p2_y)), panel_width)


class Station:
    # ... (Station class remains mostly the same) ...
    _id_counter = 0

    def __init__(self, x, y):
        self.id = Station._id_counter
        Station._id_counter += 1
        self.x = x
        self.y = y
        self.comm_radius = random.randint(MIN_STATION_COMM_RADIUS + 20, 120)
        self.size = 25
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

    def draw(self, screen_surface, is_selected):
        radius_color = COMM_RADIUS_SELECTED_COLOR if is_selected else COMM_RADIUS_COLOR
        radius_width = 2 if is_selected else 1
        pygame.draw.circle(screen_surface, radius_color, (int(self.x), int(self.y)), int(self.comm_radius), radius_width)

        self.surface.fill((0, 0, 0, 0))
        body_width, body_height = 10, 10
        body_rect = pygame.Rect((self.size // 2) - body_width // 2, (self.size // 2) - body_height // 2, body_width, body_height)
        body_color = STATION_SELECTED_COLOR if is_selected else STATION_COLOR
        pygame.draw.rect(self.surface, body_color, body_rect)
        antenna_pos = (self.size // 2, self.size // 2 - body_height // 2 - 2)
        pygame.draw.circle(self.surface, WHITE, antenna_pos, 3)

        alpha = STATION_ALPHA_SELECTED if is_selected else STATION_ALPHA_NORMAL
        self.surface.set_alpha(alpha)
        blit_pos = (int(self.x - self.size // 2), int(self.y - self.size // 2))
        screen_surface.blit(self.surface, blit_pos)

    def is_near(self, other_station):
        return math.sqrt((self.x - other_station.x) ** 2 + (self.y - other_station.y) ** 2) < STATION_MIN_DISTANCE

    def is_satellite_in_range(self, satellite):
        if satellite.status != 'operational':
            return False
        distance = math.sqrt((self.x - satellite.x) ** 2 + (self.y - satellite.y) ** 2)
        return distance <= self.comm_radius

    def change_radius(self, delta):
        self.comm_radius += delta
        self.comm_radius = max(MIN_STATION_COMM_RADIUS, min(self.comm_radius, MAX_STATION_COMM_RADIUS))


# List to store the satellites
satellites = []
# List to store the stations
stations = []

# --- Functions ---

def create_satellite(sat_type):
    # ... (create_satellite function remains the same) ...
    orbit_radius = random.uniform(MIN_ORBIT_RADIUS, MAX_ORBIT_RADIUS)
    if sat_type == 'A': speed = random.uniform(MIN_SPEED_A, MAX_SPEED_A); color = SATELLITE_BLUE
    elif sat_type == 'B': speed = random.uniform(MIN_SPEED_B, MAX_SPEED_B); color = SATELLITE_GREEN
    else: return
    if random.random() < 0.4:
        speed *= -1

    satellites.append(Satellite(orbit_radius=orbit_radius, speed=speed, color=color))
    print(f"Created Type {sat_type} satellite with radius {orbit_radius:.0f}, speed {speed:.4f}")


def add_random_station():
    # ... (add_random_station function remains the same) ...
    max_attempts = 100
    for _ in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        station_x = EARTH_POSITION[0] + EARTH_RADIUS * math.cos(angle)
        station_y = EARTH_POSITION[1] + EARTH_RADIUS * math.sin(angle)
        temp_station = Station(station_x, station_y)
        collision = any(temp_station.is_near(existing_station) for existing_station in stations)
        if not collision:
            stations.append(Station(station_x, station_y))
            print(f"Random station added at angle {math.degrees(angle):.1f} deg")
            return
    print("Could not find a free spot for a random station after multiple attempts.")


# --- Buttons ---
class Button:
    # ... (Button class remains the same) ...
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

# Create buttons
button1 = Button(20, 20, 250, 40, "Create Satellite Type A (Blue)", lambda: create_satellite('A'))
button2 = Button(20, 70, 250, 40, "Create Satellite Type B (Green)", lambda: create_satellite('B'))
button_add_station = Button(20, 120, 250, 40, "Add Random Station", add_random_station)


# --- Game Loop ---
running = True
while running:
    current_ticks = pygame.time.get_ticks()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # *** REMOVED Keyboard Input for Radius Change ***
        # if event.type == pygame.KEYDOWN:
        #     if selected_station: # Only if a station is selected
        #         # ... (removed key handling) ...

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            clicked_on_button = button1.is_hovered() or button2.is_hovered() or button_add_station.is_hovered()
            clicked_on_station = False
            station_interacted_with = None # Keep track if we interacted with a station

            # --- Left Click Handling (Button 1) ---
            if event.button == 1:
                # Handle Button Clicks FIRST
                if clicked_on_button:
                    button1.handle_click()
                    button2.handle_click()
                    button_add_station.handle_click()
                    station_interacted_with = True # Prevent station logic if button clicked

                # Handle Station Selection / Radius Increase
                if not clicked_on_button:
                    new_selection = None
                    min_dist_sq = STATION_SELECTION_RADIUS**2
                    for station in stations:
                        dist_sq = (mouse_x - station.x)**2 + (mouse_y - station.y)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            new_selection = station
                            clicked_on_station = True # Click was near *a* station

                    # --- Logic for clicking on a station ---
                    if new_selection is not None:
                         station_interacted_with = True # Mark interaction
                         # If clicking the *already selected* station, increase radius
                         if new_selection == selected_station:
                              selected_station.change_radius(STATION_RADIUS_CLICK_CHANGE)
                              print(f"Station {selected_station.id} radius increased to {selected_station.comm_radius:.0f}")
                         # Otherwise, just select the new station
                         else:
                              selected_station = new_selection
                              print(f"Station {selected_station.id} selected.")
                    # If clicking elsewhere (not button, not station), deselect
                    elif not clicked_on_button:
                         if selected_station:
                              print("Station deselected.")
                         selected_station = None


                # Handle Manual Station Placement (only if no interaction yet and inside Earth)
                if not station_interacted_with: # Includes not clicking button or existing station
                    dist_sq_to_earth_center = (mouse_x - EARTH_POSITION[0]) ** 2 + (mouse_y - EARTH_POSITION[1]) ** 2
                    if dist_sq_to_earth_center <= EARTH_RADIUS ** 2:
                        # ... (Station placement logic remains the same) ...
                        dist_to_earth_center = math.sqrt(dist_sq_to_earth_center)
                        if dist_to_earth_center > 0:
                            station_x = EARTH_POSITION[0] + (mouse_x - EARTH_POSITION[0]) * EARTH_RADIUS / dist_to_earth_center
                            station_y = EARTH_POSITION[1] + (mouse_y - EARTH_POSITION[1]) * EARTH_RADIUS / dist_to_earth_center
                        else:
                            station_x = EARTH_POSITION[0]; station_y = EARTH_POSITION[1] - EARTH_RADIUS
                        temp_station = Station(station_x, station_y)
                        collision = any(temp_station.is_near(existing_station) for existing_station in stations)
                        if not collision:
                            stations.append(Station(station_x, station_y))
                            print(f"Station added at ({station_x:.0f}, {station_y:.0f})")
                        else: print("Cannot place station too close.")

            # --- Right Click Handling (Button 3) for Radius Decrease ---
            elif event.button == 3:
                 if selected_station: # Only act if a station is selected
                      dist_sq_to_selected = (mouse_x - selected_station.x)**2 + (mouse_y - selected_station.y)**2
                      if dist_sq_to_selected < STATION_SELECTION_RADIUS**2: # Check if click is near the selected one
                           selected_station.change_radius(-STATION_RADIUS_CLICK_CHANGE) # Decrease radius
                           print(f"Station {selected_station.id} radius decreased to {selected_station.comm_radius:.0f}")


    # --- Update ---
    for sat in satellites:
        sat.update(current_ticks)

    # Remove 'destroyed' satellites
    satellites = [sat for sat in satellites if sat.status != 'destroyed']


    # --- Drawing ---
    screen.fill(DARK_SPACE)

    # Draw Stars
    for x, y, r in stars: pygame.draw.circle(screen, STAR_COLOR, (int(x), int(y)), int(r))

    # Draw Earth Image (or fallback circle)
    if earth_image:
        earth_rect = earth_image.get_rect(center=EARTH_POSITION)
        screen.blit(earth_image, earth_rect)
    else:
        pygame.draw.circle(screen, (0, 80, 180), EARTH_POSITION, EARTH_RADIUS)

    # Draw Station Radii and Bodies
    for station in stations:
        is_selected = (station == selected_station)
        station.draw(screen, is_selected)

    # Draw Satellites
    for sat in satellites:
        sat.draw(screen)

    # Draw Communication Lines
    for station in stations:
        for sat in satellites:
            if station.is_satellite_in_range(sat):
                start_pos = (int(station.x), int(station.y))
                end_pos = (int(sat.x), int(sat.y))
                pygame.draw.line(screen, COMM_LINE_COLOR, start_pos, end_pos, 1)

    # Draw UI Text (Updated Instructions)
    if selected_station:
        # *** Updated UI Text ***
        info_text = f"Selected Station ID: {selected_station.id} | Radius: {selected_station.comm_radius:.0f} (LClick: Incr, RClick: Decr)"
        info_surface = info_font.render(info_text, True, YELLOW)
        screen.blit(info_surface, (WIDTH // 2 - info_surface.get_width() // 2, 15))
    else:
         # *** Updated UI Text ***
         info_text = "LClick near station to select. LClick Earth to add manually."
         info_surface = info_font.render(info_text, True, WHITE)
         screen.blit(info_surface, (WIDTH // 2 - info_surface.get_width() // 2, 15))


    # Draw Buttons
    button1.draw(screen)
    button2.draw(screen)
    button_add_station.draw(screen)

    # --- Display Update ---
    pygame.display.flip()
    clock.tick(60)

# Quit Pygame
pygame.quit()