import pygame
import math
import random
import os  

pygame.init()

#Todo: Add capacity for station: max 3
#Todo: Add that the radius of the station will be not a circle but the Half of the circle
#Todo: Add visualization as in the papa project

WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Satellite Simulation v5 - Enhanced Visuals") # Updated caption
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
DARK_SPACE = (10, 10, 30)
SATELLITE_BLUE = (0, 100, 180)
SATELLITE_GREEN = (0, 150, 80)
BLINK_RED = (255, 50, 50)

DAMAGED_SATELLITE_COLOR = (100, 100, 100) 
DAMAGED_PANEL_COLOR = (80, 80, 80)
OPERATIONAL_PANEL_COLOR = (180, 180, 60)

WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
STAR_COLOR = (200, 200, 200)
STATION_COLOR = (120, 120, 120)
STATION_SELECTED_COLOR = (200, 200, 200)

COMM_RADIUS_COLOR = (0, 120, 0, 100)
COMM_RADIUS_SELECTED_COLOR = (0, 200, 0, 130)
COMM_LINE_COLOR = (180, 180, 180)

CAPACITY_FULL_COLOR = (255, 0, 0)
CAPACITY_NORMAL_COLOR = (0, 255, 0)

EARTH_RADIUS = 100
EARTH_POSITION = (WIDTH // 2, HEIGHT // 2)
STATION_MIN_DISTANCE = 40
MIN_STATION_COMM_RADIUS = 20
MAX_STATION_COMM_RADIUS = 300 
STATION_SELECTION_RADIUS = 20
STATION_ALPHA_NORMAL = 180
STATION_ALPHA_SELECTED = 255
STATION_RADIUS_CLICK_CHANGE = 10
STATION_MAX_CAPACITY = 3
STATION_COMM_ANGLE_DEG = 210

STATION_ARC_POLYGON_SEGMENTS = 20

MIN_ORBIT_RADIUS = EARTH_RADIUS + 30
MAX_ORBIT_RADIUS = min(WIDTH // 2, HEIGHT // 2) - 100

MIN_SPEED_A = 0.001
MAX_SPEED_A = 0.006
MIN_SPEED_B = 0.002
MAX_SPEED_B = 0.004

# Damage & Blinking
SATELLITE_DAMAGE_PROBABILITY = 0.0003
BLINK_DURATION_MS = 5000
BLINK_INTERVAL_MS = 250

STAR_COUNT = 350
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1.5)) for _ in range(STAR_COUNT)]

# Font
font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 22)
button_font = pygame.font.SysFont(None, 24)
capacity_font = pygame.font.SysFont(None, 18)

# --- Load Assets ---
# (Keep Earth loading, satellite image loading still optional)
earth_image = None

try:
    earth_image_path = 'earth_texture.png'
    if os.path.exists(earth_image_path):
        earth_image_original = pygame.image.load(earth_image_path).convert_alpha()
        earth_image = pygame.transform.scale(earth_image_original, (EARTH_RADIUS * 2, EARTH_RADIUS * 2))
    else:
        print(f"Warning: Earth image '{earth_image_path}' not found. Drawing blue circle instead.")

except pygame.error as e:
    print(f"Error loading image: {e}. Using fallback drawing.")
    earth_image = None

selected_station = None

class Satellite:
    def __init__(self, orbit_radius, speed, color):
        self.orbit_radius = orbit_radius
        self.speed = speed
        self.initial_color = color 
        self.color = color         
        self.angle = random.uniform(0, 2 * math.pi)
        self.status = 'operational'
        self.x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
        self.y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_on = False
        self.connected_to = None

    def update(self, current_ticks):
        if self.connected_to and (self.status != 'operational' or self.connected_to not in stations):
             if self.connected_to in stations:
                 self.connected_to.disconnect_satellite(self)
             self.connected_to = None

        if self.status == 'operational':
            self.angle += self.speed
            self.angle %= 2 * math.pi
            self.x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
            self.y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)
            if random.random() < SATELLITE_DAMAGE_PROBABILITY:
                self.status = 'damaging'
                self.is_blinking = True
                self.blink_start_time = current_ticks
                if self.connected_to:
                    self.connected_to.disconnect_satellite(self)
                    self.connected_to = None

        elif self.status == 'damaging':
            elapsed_blink_time = current_ticks - self.blink_start_time
            if elapsed_blink_time > BLINK_DURATION_MS:
                self.status = 'destroyed'
                self.is_blinking = False
            else:
                self.blink_on = (elapsed_blink_time // BLINK_INTERVAL_MS) % 2 == 0

    def draw(self, surface):
        if self.status == 'destroyed':
            return

        x, y = int(self.x), int(self.y)

        body_radius = 6
        panel_length = 12 
        panel_width = 3

        # Determine current body color
        current_body_color = self.initial_color # Start with operational color
        if self.status == 'damaging':
            current_body_color = BLINK_RED if self.blink_on else DAMAGED_SATELLITE_COLOR
        elif self.status == 'operational':
             current_body_color = self.initial_color # Use its assigned color (Blue or Green)

        # Draw the central body
        pygame.draw.circle(surface, current_body_color, (x, y), body_radius)

        # Determine panel color and if they should be drawn
        draw_panels = True
        panel_color = OPERATIONAL_PANEL_COLOR
        if self.status == 'damaging':
            if self.blink_on:
                panel_color = BLINK_RED
            else: 
                panel_color = DAMAGED_PANEL_COLOR

        if draw_panels:
            panel_angle_rad = self.angle + math.pi / 2

            p1_start_x = x + math.cos(panel_angle_rad) * body_radius
            p1_start_y = y + math.sin(panel_angle_rad) * body_radius
            p1_end_x = x + math.cos(panel_angle_rad) * (body_radius + panel_length)
            p1_end_y = y + math.sin(panel_angle_rad) * (body_radius + panel_length)

            p2_start_x = x - math.cos(panel_angle_rad) * body_radius
            p2_start_y = y - math.sin(panel_angle_rad) * body_radius
            p2_end_x = x - math.cos(panel_angle_rad) * (body_radius + panel_length)
            p2_end_y = y - math.sin(panel_angle_rad) * (body_radius + panel_length)

            pygame.draw.line(surface, panel_color, (int(p1_start_x), int(p1_start_y)), (int(p1_end_x), int(p1_end_y)), panel_width)
            pygame.draw.line(surface, panel_color, (int(p2_start_x), int(p2_start_y)), (int(p2_end_x), int(p2_end_y)), panel_width)

        if self.connected_to:
             pygame.draw.line(surface, COMM_LINE_COLOR, (x, y),
                              (int(self.connected_to.x), int(self.connected_to.y)), 1)


class Station:
    _id_counter = 0

    def __init__(self, x, y):
        self.id = Station._id_counter
        Station._id_counter += 1
        self.x = x
        self.y = y
        self.comm_radius = random.randint(MIN_STATION_COMM_RADIUS + 20, 120)
        self.size = 25
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.capacity = STATION_MAX_CAPACITY
        self.connected_satellites = []

        dx = self.x - EARTH_POSITION[0]
        dy = self.y - EARTH_POSITION[1]
        self.base_angle_rad = math.atan2(dy, dx)


    def draw(self, screen_surface, is_selected):
        radius_color_tuple = COMM_RADIUS_SELECTED_COLOR if is_selected else COMM_RADIUS_COLOR

        if is_selected:
            radius_color_tuple = (0, 200, 0, 60)
        else:
            radius_color_tuple = (0, 120, 0, 30)   

        radius_color = pygame.Color(*radius_color_tuple) # Includes alpha

        if self.comm_radius > 0:
            radius_surface_size = int(self.comm_radius * 2) + 4
            radius_surface = pygame.Surface((radius_surface_size, radius_surface_size), pygame.SRCALPHA)
            arc_center_x = radius_surface_size // 2
            arc_center_y = radius_surface_size // 2
            center_point_on_surface = (arc_center_x, arc_center_y)

            total_arc_angle_rad = math.radians(STATION_COMM_ANGLE_DEG)
            angle_start_math = self.base_angle_rad - total_arc_angle_rad / 2
            angle_end_math = self.base_angle_rad + total_arc_angle_rad / 2 

            # Calculate points for the polygon
            polygon_points = [center_point_on_surface] 
            num_segments = STATION_ARC_POLYGON_SEGMENTS
            angle_step = total_arc_angle_rad / num_segments

            for i in range(num_segments + 1):
                current_math_angle = angle_start_math + i * angle_step
                px = arc_center_x + self.comm_radius * math.cos(current_math_angle)
                py = arc_center_y + self.comm_radius * math.sin(current_math_angle)
                polygon_points.append((int(px), int(py)))

            if len(polygon_points) >= 3:
                try:
                    pygame.draw.polygon(radius_surface, radius_color, polygon_points)
                except Exception as e:
                    print(f"Warning: Could not draw polygon for station {self.id} - {e}")        
            outline_color = (20, 70, 20)  # Light green dashed line

            for i in range(1, len(polygon_points) - 1):
                if i % 2 == 0: 
                    start = polygon_points[i]
                    end = polygon_points[i + 1]
                    pygame.draw.line(radius_surface, outline_color, start, end, 3)

            arc_blit_pos = (int(self.x - arc_center_x), int(self.y - arc_center_y))
            screen_surface.blit(radius_surface, arc_blit_pos)

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

        # --- Draw Capacity Indicator (same as before) ---
        capacity_text = f"{len(self.connected_satellites)}/{self.capacity}"
        cap_color = CAPACITY_NORMAL_COLOR if len(self.connected_satellites) < self.capacity else CAPACITY_FULL_COLOR
        capacity_surface = capacity_font.render(capacity_text, True, cap_color)
        capacity_pos = (blit_pos[0] + self.size // 2 - capacity_surface.get_width() // 2, blit_pos[1] + self.size + 2)
        screen_surface.blit(capacity_surface, capacity_pos)


    # --- Other Station methods (is_near, is_satellite_in_range, etc.) remain unchanged ---
    def is_near(self, other_station):
        return math.dist((self.x, self.y), (other_station.x, other_station.y)) < STATION_MIN_DISTANCE

    def is_satellite_in_range(self, satellite):
        if satellite.status != 'operational':
            return False
        distance = math.dist((self.x, self.y), (satellite.x, satellite.y))
        if distance > self.comm_radius:
            return False

        dx_sat = satellite.x - self.x
        dy_sat = satellite.y - self.y
        angle_to_sat = math.atan2(dy_sat, dx_sat)

        arc_angle_rad = math.radians(STATION_COMM_ANGLE_DEG)
        start_angle = self.base_angle_rad - arc_angle_rad / 2
        end_angle = self.base_angle_rad + arc_angle_rad / 2

        def normalize_angle_diff(a1, a2):
            diff = a1 - a2
            while diff <= -math.pi: diff += 2 * math.pi
            while diff > math.pi: diff -= 2 * math.pi
            return diff

        angle_diff_start = normalize_angle_diff(angle_to_sat, start_angle)
        angle_diff_end = normalize_angle_diff(angle_to_sat, end_angle)
        arc_width_check = normalize_angle_diff(end_angle, start_angle)

        if arc_width_check >= 0:
             # Check if angle is within the arc using normalized differences
             return angle_diff_start >= -1e-9 and angle_diff_end <= 1e-9 # Use tolerance for float comparison
        else: # Arc wraps around the -pi/pi boundary
             return angle_diff_start >= -1e-9 or angle_diff_end <= 1e-9

    def can_connect(self):
        return len(self.connected_satellites) < self.capacity

    def connect_satellite(self, satellite):
        if self.can_connect() and satellite not in self.connected_satellites and satellite.status == 'operational':
            self.connected_satellites.append(satellite)
            satellite.connected_to = self
            return True
        return False

    def disconnect_satellite(self, satellite):
        if satellite in self.connected_satellites:
            self.connected_satellites.remove(satellite)
            if satellite.connected_to == self:
                satellite.connected_to = None

    def disconnect_all(self):
        for sat in list(self.connected_satellites):
            self.disconnect_satellite(sat)

    def change_radius(self, delta):
        self.comm_radius += delta
        self.comm_radius = max(MIN_STATION_COMM_RADIUS, min(self.comm_radius, MAX_STATION_COMM_RADIUS))


satellites = []
stations = []

# Functions (create_satellite, add_random_station, find_closest_available_station) 
def create_satellite(sat_type):
    orbit_radius = random.uniform(MIN_ORBIT_RADIUS, MAX_ORBIT_RADIUS)
    if sat_type == 'A': speed = random.uniform(MIN_SPEED_A, MAX_SPEED_A); color = SATELLITE_BLUE
    elif sat_type == 'B': speed = random.uniform(MIN_SPEED_B, MAX_SPEED_B); color = SATELLITE_GREEN
    else: return
    if random.random() < 0.4:
        speed *= -1
    satellites.append(Satellite(orbit_radius=orbit_radius, speed=speed, color=color))
    print(f"Created Type {sat_type} satellite with radius {orbit_radius:.0f}, speed {speed:.4f}")

def add_random_station():
    max_attempts = 100
    for _ in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        station_x = EARTH_POSITION[0] + EARTH_RADIUS * math.cos(angle)
        station_y = EARTH_POSITION[1] + EARTH_RADIUS * math.sin(angle)
        can_place = True
        for existing_station in stations:
            if math.dist((station_x, station_y), (existing_station.x, existing_station.y)) < STATION_MIN_DISTANCE:
                can_place = False
                break
        if can_place:
            stations.append(Station(station_x, station_y))
            print(f"Random station added at angle {math.degrees(angle):.1f} deg")
            return
    print("Could not find a free spot for a random station after multiple attempts.")

def find_closest_available_station(satellite):
    best_station = None
    min_dist_sq = float('inf')
    for station in stations:
        if station.can_connect() and station.is_satellite_in_range(satellite):
            dist_sq = (station.x - satellite.x)**2 + (station.y - satellite.y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_station = station
    return best_station

# --- Buttons ---
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

button1 = Button(20, 20, 250, 40, "Create Satellite Type A (Blue)", lambda: create_satellite('A'))
button2 = Button(20, 70, 250, 40, "Create Satellite Type B (Green)", lambda: create_satellite('B'))
button_add_station = Button(20, 120, 250, 40, "Add Random Station", add_random_station)


# --- Game Loop ---
running = True
while running:
    current_ticks = pygame.time.get_ticks()

    # --- Event Handling (remains unchanged) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            clicked_on_button = button1.is_hovered() or button2.is_hovered() or button_add_station.is_hovered()
            station_interacted_with = False # Reset interaction flag

            # Left Click
            if event.button == 1:
                if clicked_on_button:
                    button1.handle_click()
                    button2.handle_click()
                    button_add_station.handle_click()
                    station_interacted_with = True
                else:
                    # Station selection/radius increase logic
                    new_selection = None
                    min_dist_sq = STATION_SELECTION_RADIUS**2
                    for station in stations:
                        dist_sq = (mouse_x - station.x)**2 + (mouse_y - station.y)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            new_selection = station

                    if new_selection:
                        station_interacted_with = True
                        if new_selection == selected_station:
                            selected_station.change_radius(STATION_RADIUS_CLICK_CHANGE)
                        else:
                            selected_station = new_selection
                    elif not clicked_on_button: 
                         selected_station = None


                    # Manual station placement
                    if not station_interacted_with:
                        dist_to_earth_center = math.dist((mouse_x, mouse_y), EARTH_POSITION)
                        if abs(dist_to_earth_center - EARTH_RADIUS) < 20:
                            if dist_to_earth_center > 0:
                                factor = EARTH_RADIUS / dist_to_earth_center
                                station_x = EARTH_POSITION[0] + (mouse_x - EARTH_POSITION[0]) * factor
                                station_y = EARTH_POSITION[1] + (mouse_y - EARTH_POSITION[1]) * factor
                            else:
                                station_x = EARTH_POSITION[0]
                                station_y = EARTH_POSITION[1] - EARTH_RADIUS

                            can_place = True
                            for existing_station in stations:
                                if math.dist((station_x, station_y), (existing_station.x, existing_station.y)) < STATION_MIN_DISTANCE:
                                    can_place = False
                                    print("Cannot place station: Too close to another station.")
                                    break
                            if can_place:
                                stations.append(Station(station_x, station_y))
                                print(f"Station added manually near ({station_x:.0f}, {station_y:.0f})")

            # Right Click
            elif event.button == 3:
                 if selected_station:
                     dist_sq_to_selected = (mouse_x - selected_station.x)**2 + (mouse_y - selected_station.y)**2
                     if dist_sq_to_selected < STATION_SELECTION_RADIUS**2:
                         selected_station.change_radius(-STATION_RADIUS_CLICK_CHANGE)
                         station_interacted_with = True # Count as interaction


    # --- Update Logic
    for sat in satellites:
        sat.update(current_ticks)
    satellites = [sat for sat in satellites if sat.status != 'destroyed']
    for station in stations:
        for sat in list(station.connected_satellites):
            if not station.is_satellite_in_range(sat):
                station.disconnect_satellite(sat)
    for sat in satellites:
        if sat.status == 'operational' and not sat.connected_to:
            best_station = find_closest_available_station(sat)
            if best_station:
                best_station.connect_satellite(sat)


    # --- Drawing ---
    screen.fill(DARK_SPACE)
    for x, y, r in stars: pygame.draw.circle(screen, STAR_COLOR, (int(x), int(y)), int(r))

    if earth_image:
        earth_rect = earth_image.get_rect(center=EARTH_POSITION)
        screen.blit(earth_image, earth_rect)
    else:
        pygame.draw.circle(screen, (0, 80, 180), EARTH_POSITION, EARTH_RADIUS)

    for station in stations:
        is_selected = (station == selected_station)
        station.draw(screen, is_selected)

    for sat in satellites:
        sat.draw(screen)

    # Draw UI Text (remains unchanged)
    if selected_station:
        conn_count = len(selected_station.connected_satellites)
        cap = selected_station.capacity
        info_text = (f"Selected Station ID: {selected_station.id} | "
                     f"Radius: {selected_station.comm_radius:.0f} (L/R Click Icon: Change) | "
                     f"Connections: {conn_count}/{cap}")
        info_surface = info_font.render(info_text, True, YELLOW)
        screen.blit(info_surface, (WIDTH // 2 - info_surface.get_width() // 2, 15))
    else:
         info_text = "LClick station icon to select/increase radius. LClick near Earth edge to add manually."
         info_surface = info_font.render(info_text, True, WHITE)
         screen.blit(info_surface, (WIDTH // 2 - info_surface.get_width() // 2, 15))

    # Draw Buttons
    button1.draw(screen)
    button2.draw(screen)
    button_add_station.draw(screen)

    pygame.display.flip()
    clock.tick(60)

for station in stations:
    station.disconnect_all()
pygame.quit()