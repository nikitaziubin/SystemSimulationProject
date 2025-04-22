import pygame
import random
from config import *
from satellite import *
from station import *
import math
import os


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 22)
button_font = pygame.font.SysFont(None, 24)
capacity_font = pygame.font.SysFont(None, 18)
selected_station = None
delta_time = clock.tick(60)

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
        sat.update(current_ticks, stations, delta_time)

    for station in stations:
        station.update(current_ticks)


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
        station.draw(screen, is_selected, capacity_font)

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