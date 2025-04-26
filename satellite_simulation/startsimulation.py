from satellite import Satellite
from station import Station
from config import *
import math
import random
import time
from inputbox import InputBox
from button import Button

#pygame.init()
FONT = pygame.font.Font(None, 26)
screen = pygame.display.set_mode((800, 700))
clock = pygame.time.Clock()
scroll_offset = 0
scroll_speed = 20


def start_simulation(satellites, stations, disable_manual_controls_callback, params):
    num_stations = int(params["stations"])
    duration_minutes = int(params["duration"])
    duration_seconds = int(params["duration_seconds"])

    # Disable manual controls
    disable_manual_controls_callback()

    # Create stations
    for _ in range(num_stations):
        angle = random.uniform(0, 2 * math.pi)
        x = EARTH_POSITION[0] + EARTH_RADIUS * math.cos(angle)
        y = EARTH_POSITION[1] + EARTH_RADIUS * math.sin(angle)
        stations.append(Station(x, y))

    # Create satellites from custom configs
    if "custom_satellites" in params:
        for orbit_radius, speed, color in params["custom_satellites"]:
            satellites.append(Satellite(orbit_radius, speed, color))

    # Store simulation start time
    start_time = time.time()
    simulation_end_time = start_time + (duration_minutes * 60 + duration_seconds)

    return simulation_end_time



def show_simulation_popup():
    input_boxes = [
        InputBox(100, 100, 140, 32, "Green Satellites:", "0"),
        InputBox(100, 160, 140, 32, "Blue Satellites:", "0"),
        InputBox(100, 220, 140, 32, "Stations:", "0"),
        InputBox(100, 280, 140, 32, "Duration (min):", "0"),
        InputBox(100, 340, 140, 32, "Duration (sec):", "30")
    ]

    satellite_configs = []
    scroll_offset = 0
    confirmed = False
    cancelled = False

    def confirm():
        nonlocal confirmed
        confirmed = True

    def cancel():
        nonlocal cancelled
        cancelled = True

    ok_button = Button(100, 400, 140, 40, "Start", confirm)
    back_button = Button(260, 400, 140, 40, "Back", cancel)
    add_sat_button = Button(500, 40, 140, 35, "Add Satellite", lambda: satellite_configs.append(SatelliteConfig(500, 0)))

    popup_running = True

    while popup_running:
        screen.fill((30, 30, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.is_hovered():
                    confirm()
                    popup_running = False
                elif back_button.is_hovered():
                    cancel()
                    popup_running = False
                elif add_sat_button.is_hovered():
                    add_sat_button.handle_click()

            elif event.type == pygame.MOUSEWHEEL:
                scroll_offset += event.y * 20

            for box in input_boxes:
                box.handle_event(event)

            for i, config in enumerate(satellite_configs):
                config.handle_event(event, scroll_offset, base_y=100 + i * 80)
            to_remove = None
            for config in satellite_configs:
                if event.type == pygame.MOUSEBUTTONDOWN and config.remove_button.is_hovered():
                    to_remove = config
            if to_remove:
                satellite_configs.remove(to_remove)


        # Draw elements
        for box in input_boxes:
            box.draw(screen)

        ok_button.draw(screen)
        back_button.draw(screen)
        add_sat_button.draw(screen)

        for i, config in enumerate(satellite_configs):
            config.draw(screen, scroll_offset, base_y=100 + i * 80)

        pygame.display.flip()
        clock.tick(30)

    if cancelled:
        return None

    simulation_params = {
        "green": input_boxes[0].get_value(),
        "blue": input_boxes[1].get_value(),
        "stations": input_boxes[2].get_value(),
        "duration": input_boxes[3].get_value(),
        "duration_seconds": input_boxes[4].get_value(),
        "custom_satellites": [cfg.get_values() for cfg in satellite_configs]
    }

    print("Simulation parameters:", simulation_params)
    return simulation_params


class SatelliteConfig:
    def __init__(self, x, y):
        self.base_x = x
        self.base_y = y
        self.orbit_box = InputBox(x, y, 100, 30, "Orbit Radius", "200", is_float=True)
        self.speed_box = InputBox(x + 110, y, 100, 30, "Speed", "0.002", is_float=True)
        self.color_options = ["Green", "Blue"]
        self.selected_color_index = 0
        self.dropdown_rect = pygame.Rect(x + 220, y, 100, 30)
        self.remove_button = Button(x + 330, y, 30, 30, "X", None)  # 'X' button


    def handle_event(self, event, scroll_offset, base_y):
        y = base_y + scroll_offset
        self.orbit_box.rect.y = y
        self.speed_box.rect.y = y
        self.dropdown_rect.y = y
        self.remove_button.rect.y = y 

        self.orbit_box.handle_event(event)
        self.speed_box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and self.dropdown_rect.collidepoint(event.pos):
            self.selected_color_index = (self.selected_color_index + 1) % len(self.color_options)

    def draw(self, screen, scroll_offset, base_y):
        y = base_y + scroll_offset
        self.orbit_box.rect.y = y
        self.speed_box.rect.y = y
        self.dropdown_rect.y = y

        # Draw labels
        orbit_label = FONT.render("Radius           Speed", True, pygame.Color('white'))
        speed_label = FONT.render("                      Color", True, pygame.Color('white'))

        screen.blit(orbit_label, (self.orbit_box.rect.x, self.orbit_box.rect.y - 20))
        screen.blit(speed_label, (self.speed_box.rect.x, self.speed_box.rect.y - 20))

        # Draw input boxes and dropdown
        self.orbit_box.draw(screen)
        self.speed_box.draw(screen)
        pygame.draw.rect(screen, pygame.Color('gray'), self.dropdown_rect, 2)
        color_label = FONT.render(self.color_options[self.selected_color_index], True, pygame.Color('white'))
        screen.blit(color_label, (self.dropdown_rect.x + 5, self.dropdown_rect.y + 5))
        self.remove_button.draw(screen)



    def get_values(self):
        orbit = self.orbit_box.get_value()
        speed = self.speed_box.get_value()
        color = SATELLITE_GREEN if self.color_options[self.selected_color_index] == "Green" else SATELLITE_BLUE
        return orbit, speed, color
