#from main import show_simulation_popup
from satellite import Satellite
from station import Station
from config import *
import math
import random
import time
from inputbox import InputBox
from button import Button



def start_simulation(satellites, stations, disable_manual_controls_callback, params):
    num_green = int(params["green"])
    num_blue = int(params["blue"])
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

    # Create satellites
    for _ in range(num_green):
        orbit_radius = random.uniform(MIN_ORBIT_RADIUS, MAX_ORBIT_RADIUS)
        speed = random.uniform(MIN_SPEED_B, MAX_SPEED_B)
        satellites.append(Satellite(orbit_radius, speed, SATELLITE_GREEN))

    for _ in range(num_blue):
        orbit_radius = random.uniform(MIN_ORBIT_RADIUS, MAX_ORBIT_RADIUS)
        speed = random.uniform(MIN_SPEED_A, MAX_SPEED_A)
        satellites.append(Satellite(orbit_radius, speed, SATELLITE_BLUE))

    # Store simulation start time
    start_time = time.time()
    simulation_end_time = start_time + (duration_minutes * 60 + duration_seconds)

    return simulation_end_time 



def show_simulation_popup():
    input_boxes = [
        InputBox(100, 100, 140, 32, "Green Satellites:", "5"),
        InputBox(100, 160, 140, 32, "Blue Satellites:", "5"),
        InputBox(100, 220, 140, 32, "Stations:", "3"),
        InputBox(100, 280, 140, 32, "Duration (min):", "0"),
        InputBox(100, 340, 140, 32, "Duration (sec):", "30")]

    confirmed = False  # Track whether the Start button was clicked

    def confirm():
        nonlocal confirmed
        confirmed = True

    ok_button = Button(100, 400, 140, 40, "Start", confirm)

    popup_running = True

    while popup_running:
        screen.fill((30, 30, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN and ok_button.is_hovered():
                popup_running = False  # Exit and continue simulation
            for box in input_boxes:
                box.handle_event(event)

        for box in input_boxes:
            box.draw(screen)

        ok_button.draw(screen)

        pygame.display.flip()
        clock.tick(30)

    # Retrieve values (you can return them or store them globally)
    simulation_params = {
        "green": input_boxes[0].get_value(),
        "blue": input_boxes[1].get_value(),
        "stations": input_boxes[2].get_value(),
        "duration": input_boxes[3].get_value(),
        "duration_seconds": input_boxes[4].get_value()
    }

    print("Simulation parameters:", simulation_params)
    return simulation_params