from satellite import Satellite
from station import Station
from config import *
import math
import random
import time
from inputbox import InputBox
from button import Button

pygame.init()
FONT = pygame.font.Font(None, 26)
screen = pygame.display.set_mode((800, 700))
clock = pygame.time.Clock()
scroll_offset = 0
scroll_speed = 20

def start_simulation(satellites, stations, disable_manual_controls_callback, params):
    duration_minutes = int(params["duration"])
    duration_seconds = int(params["duration_seconds"])
    damage_probability = float(params.get("damage_probability", 0.001))
    recovery_time_seconds = float(params.get("recovery_time_seconds", 5)) 


    disable_manual_controls_callback()

    Station.station_damage_probability = damage_probability
    Station.station_repair_time_ms = recovery_time_seconds * 1000 
    Satellite.satellite_damage_probability = float(params.get("satellite_damage_probability", 0.001))
    Satellite.satellite_repair_time_seconds = float(params.get("satellite_recovery_time_seconds", 5))

    if "custom_satellites" in params:
        for name, orbit_radius, speed, color in params["custom_satellites"]:
            satellites.append(Satellite(orbit_radius, speed, color, name))

    start_time = time.time()
    simulation_end_time = start_time + (duration_minutes * 60 + duration_seconds)

    return simulation_end_time

def show_simulation_popup():
    satellite_name_counter = 1

    input_boxes = [
        InputBox(100, 200, 140, 32, "Duration (min):", "5"),
        InputBox(100, 260, 140, 32, "Duration (sec):", "0"),
        InputBox(100, 320, 140, 32, "Recover Station Time (sec):", "5", is_float=True),
        InputBox(100, 380, 140, 32, "Damage Station Prob (%):", "1", is_float=True),
        InputBox(100, 440, 140, 32, "Recover Satellite Time (sec):", "5", is_float=True),
        InputBox(100, 500, 140, 32, "Damage Satellite Prob (%):", "0.3", is_float=True)]

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

    def add_satellite_config():
        nonlocal satellite_name_counter
        name = f"S{satellite_name_counter}"
        satellite_configs.append(SatelliteConfig(500, 0, name))
        satellite_name_counter += 1

    ok_button = Button(100, 600, 140, 40, "Start", confirm)
    back_button = Button(260, 600, 140, 40, "Back", cancel)
    add_sat_button = Button(500, 40, 140, 35, "Add Satellite", add_satellite_config)

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

        # Draw input fields
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
        "duration": input_boxes[0].get_value(),
        "duration_seconds": input_boxes[1].get_value(),
        "recovery_time_seconds": input_boxes[2].get_value(),
        "damage_probability": input_boxes[3].get_value() / 1000,
        "satellite_recovery_time_seconds": input_boxes[4].get_value(),
        "satellite_damage_probability": input_boxes[5].get_value() / 1000,
        "custom_satellites": [cfg.get_values() for cfg in satellite_configs]
}



    print("Simulation parameters:", simulation_params)
    return simulation_params

class SatelliteConfig:
    def __init__(self, x, y, default_name="S"):
        self.base_x = x
        self.base_y = y
        self.orbit_box = InputBox(x, y, 100, 30, "Radius", "250", is_float=True)
        self.speed_box = InputBox(x + 110, y, 100, 30, "Speed", "0.002", is_float=True)
        self.dropdown_rect = pygame.Rect(x + 220, y, 100, 30)  # Color Dropdown
        self.name_box = InputBox(x + 330, y, 100, 30, "Name", default_name)
        self.remove_button = Button(x + 440, y, 30, 30, "X", None)

        self.color_options = ["Green", "Blue"]
        self.selected_color_index = 0

    def handle_event(self, event, scroll_offset, base_y):
        y = base_y + scroll_offset
        self.orbit_box.rect.y = y
        self.speed_box.rect.y = y
        self.dropdown_rect.y = y
        self.name_box.rect.y = y
        self.remove_button.rect.y = y

        self.orbit_box.handle_event(event)
        self.speed_box.handle_event(event)
        self.name_box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and self.dropdown_rect.collidepoint(event.pos):
            self.selected_color_index = (self.selected_color_index + 1) % len(self.color_options)

    def draw(self, screen, scroll_offset, base_y):
        y = base_y + scroll_offset
        self.orbit_box.rect.y = y
        self.speed_box.rect.y = y
        self.dropdown_rect.y = y
        self.name_box.rect.y = y
        self.remove_button.rect.y = y

        # Draw labels (top once)
        labels = FONT.render("Radius           Speed            Color             Name", True, pygame.Color('white'))
        screen.blit(labels, (self.orbit_box.rect.x, self.orbit_box.rect.y - 20))

        # Draw boxes and dropdown
        self.orbit_box.draw(screen)
        self.speed_box.draw(screen)
        pygame.draw.rect(screen, pygame.Color('gray'), self.dropdown_rect, 2)
        color_label = FONT.render(self.color_options[self.selected_color_index], True, pygame.Color('white'))
        screen.blit(color_label, (self.dropdown_rect.x + 5, self.dropdown_rect.y + 5))

        self.name_box.draw(screen)
        self.remove_button.draw(screen)

    def get_values(self):
        name = self.name_box.text
        orbit = self.orbit_box.get_value()
        speed = self.speed_box.get_value()
        color = SATELLITE_GREEN if self.color_options[self.selected_color_index] == "Green" else SATELLITE_BLUE
        return name, orbit, speed, color
