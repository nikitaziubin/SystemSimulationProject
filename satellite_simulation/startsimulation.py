from satellite import Satellite # Updated Satellite class
from station import Station
from config import * # Import SATELLITE_BLUE, SATELLITE_GREEN etc.
import math
import random
import time
from inputbox import InputBox
from button import Button
import pygame

# Initialize pygame if not already done (or ensure it's done in main)
# pygame.init()

POPUP_WIDTH, POPUP_HEIGHT = 500, 600
popup_screen = None
popup_clock = pygame.time.Clock()
popup_font = pygame.font.Font(None, 26)
satellite_counter = 0
# --- start_simulation function ---
def start_simulation(satellites_list, stations_list, disable_manual_controls_callback, params):
    # --- ADD global declaration here ---
    # This tells the function to use the 'satellite_counter' variable
    # defined in the global scope (which should be in main.py)
    global satellite_counter
    # --- End global declaration ---

    # Get simulation parameters (unchanged)
    duration_minutes = int(params["duration"])
    duration_seconds = int(params["duration_seconds"])
    num_satellites = int(params["num_satellites"])
    num_stations = int(params["num_stations"])
    station_damage_prob = float(params.get("station_damage_prob", Station.station_damage_probability))
    station_recovery_sec = float(params.get("station_recovery_time_sec", Station.station_repair_time_ms / 1000.0))
    satellite_damage_prob = float(params.get("satellite_damage_prob", Satellite.satellite_damage_probability))
    satellite_recovery_sec = float(params.get("satellite_recovery_time_sec", Satellite.satellite_repair_time_seconds))

    # Apply overrides (unchanged)
    Station.station_damage_probability = station_damage_prob
    Station.station_repair_time_ms = station_recovery_sec * 1000
    Satellite.satellite_damage_probability = satellite_damage_prob
    Satellite.satellite_repair_time_seconds = satellite_recovery_sec

    # --- Create Stations (Unchanged) ---
    stations_list.clear()
    Station._id_counter = 0
    # ... (station creation loop is identical to previous version) ...
    for i in range(num_stations):
        max_attempts = 50
        placed = False
        for _ in range(max_attempts):
            angle = random.uniform(0, 2 * math.pi)
            station_x = EARTH_POSITION[0] + EARTH_RADIUS_PIXELS * math.cos(angle)
            station_y = EARTH_POSITION[1] + EARTH_RADIUS_PIXELS * math.sin(angle)
            can_place = True
            for existing_station in stations_list:
                if math.dist((station_x, station_y), (existing_station.x, existing_station.y)) < STATION_MIN_DISTANCE:
                    can_place = False
                    break
            if can_place:
                stations_list.append(Station(station_x, station_y))
                placed = True
                break
        if not placed:
            print(f"Warning: Could not place station {i+1} without overlap after {max_attempts} attempts.")


    # --- Create Satellites (Uses global satellite_counter now) ---
    satellites_list.clear()
    # --- REMOVED the try...except block for satellite_counter ---
    # The 'global' keyword handles making it accessible.
    # Ensure it's reset in main.py before this function is called.

    altitudes_km = KUIPER_ALTITUDES_KM

    for i in range(num_satellites):
        altitude = altitudes_km[i % len(altitudes_km)]
        initial_angle = (2 * math.pi / num_satellites) * i if num_satellites > 0 else 0

        sat_type = random.choice(['A', 'B'])
        color = SATELLITE_BLUE if sat_type == 'A' else SATELLITE_GREEN
        prefix = "COM" if sat_type == 'A' else "MIL"

        # This line should now work correctly
        name = f"{prefix}-{satellite_counter}"

        satellites_list.append(Satellite(altitude_km=altitude, name=name, color=color, initial_angle=initial_angle))

        # Increment the global counter directly
        satellite_counter += 1

    # --- Rest of the function is unchanged ---
    disable_manual_controls_callback()
    start_time = time.time()
    simulation_end_time = start_time + (duration_minutes * 60) + duration_seconds
    print(f"--- Simulation Setup ---")
    # ... (print statements are identical) ...
    print(f"Duration: {duration_minutes}m {duration_seconds}s")
    print(f"Satellites: {len(satellites_list)} (Altitudes: {KUIPER_ALTITUDES_KM} km)")
    print(f"Stations: {len(stations_list)}")
    print(f"Station Damage Prob: {Station.station_damage_probability:.4f}, Repair Time: {Station.station_repair_time_ms / 1000.0:.1f}s")
    print(f"Satellite Damage Prob: {Satellite.satellite_damage_probability:.4f}, Repair Time: {Satellite.satellite_repair_time_seconds:.1f}s")
    print(f"------------------------")

    return simulation_end_time


# --- show_simulation_popup function (Unchanged from previous step) ---
def show_simulation_popup():
    # (Code is identical to the previous version provided)
    # ... [rest of show_simulation_popup function] ...
    global popup_screen

    main_screen = pygame.display.get_surface()
    if not main_screen:
         print("Error: Main display surface not found.")
         return None

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    popup_rect = pygame.Rect((WIDTH - POPUP_WIDTH) // 2, (HEIGHT - POPUP_HEIGHT) // 2, POPUP_WIDTH, POPUP_HEIGHT)
    popup_color = (40, 40, 60)

    input_boxes = [
        InputBox(popup_rect.x + 50, popup_rect.y + 50, 140, 32, "Duration (min):", "10"),
        InputBox(popup_rect.x + 250, popup_rect.y + 50, 140, 32, "Duration (sec):", "0"),
        InputBox(popup_rect.x + 50, popup_rect.y + 120, 140, 32, "Num Satellites:", "27"),
        InputBox(popup_rect.x + 250, popup_rect.y + 120, 140, 32, "Num Stations:", "12"),
        InputBox(popup_rect.x + 50, popup_rect.y + 220, 200, 32, "Station Recover Time (s):", f"{Station.station_repair_time_ms / 1000.0:.1f}", is_float=True),
        InputBox(popup_rect.x + 50, popup_rect.y + 280, 200, 32, "Station Damage Prob (%):", f"{Station.station_damage_probability * 100:.2f}", is_float=True),
        InputBox(popup_rect.x + 50, popup_rect.y + 340, 200, 32, "Satellite Recover Time (s):", f"{Satellite.satellite_repair_time_seconds:.1f}", is_float=True),
        InputBox(popup_rect.x + 50, popup_rect.y + 400, 200, 32, "Satellite Damage Prob (%):", f"{Satellite.satellite_damage_probability * 100:.2f}", is_float=True),
    ]

    confirmed = False
    cancelled = False

    def confirm():
        nonlocal confirmed
        try:
             int(input_boxes[0].get_value())
             int(input_boxes[1].get_value())
             int(input_boxes[2].get_value())
             int(input_boxes[3].get_value())
             confirmed = True
        except ValueError:
             print("Invalid input. Please enter numbers for duration, satellites, and stations.")

    def cancel():
        nonlocal cancelled
        cancelled = True

    ok_button = Button(popup_rect.centerx - 150, popup_rect.bottom - 70, 120, 40, "Start Sim", confirm)
    back_button = Button(popup_rect.centerx + 30, popup_rect.bottom - 70, 120, 40, "Cancel", cancel)

    popup_running = True
    while popup_running:
        main_screen.blit(overlay, (0, 0))
        pygame.draw.rect(main_screen, popup_color, popup_rect, border_radius=10)
        pygame.draw.rect(main_screen, WHITE, popup_rect, width=2, border_radius=10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.is_hovered():
                    ok_button.handle_click()
                    if confirmed:
                         popup_running = False
                elif back_button.is_hovered():
                    back_button.handle_click()
                    popup_running = False
            for box in input_boxes:
                box.handle_event(event)

        title_surf = popup_font.render("Simulation Configuration", True, WHITE)
        main_screen.blit(title_surf, (popup_rect.centerx - title_surf.get_width() // 2, popup_rect.y + 10))

        for box in input_boxes:
            box.draw(main_screen)

        ok_button.draw(main_screen)
        back_button.draw(main_screen)

        pygame.display.flip()
        popup_clock.tick(30)

    if cancelled:
        return None

    simulation_params = {
        "duration": input_boxes[0].get_value(),
        "duration_seconds": input_boxes[1].get_value(),
        "num_satellites": input_boxes[2].get_value(),
        "num_stations": input_boxes[3].get_value(),
        "station_recovery_time_sec": input_boxes[4].get_value(),
        "station_damage_prob": input_boxes[5].get_value(), # % input
        "satellite_recovery_time_sec": input_boxes[6].get_value(),
        "satellite_damage_prob": input_boxes[7].get_value(), # % input
    }

    # Convert probabilities and handle defaults (Unchanged logic)
    sim_params_st_dmg_prob = simulation_params["station_damage_prob"]
    simulation_params["station_damage_prob"] = sim_params_st_dmg_prob / 100.0 if sim_params_st_dmg_prob else Station.station_damage_probability

    sim_params_sat_dmg_prob = simulation_params["satellite_damage_prob"]
    simulation_params["satellite_damage_prob"] = sim_params_sat_dmg_prob / 100.0 if sim_params_sat_dmg_prob else Satellite.satellite_damage_probability

    sim_params_st_rec_time = simulation_params["station_recovery_time_sec"]
    simulation_params["station_recovery_time_sec"] = sim_params_st_rec_time if sim_params_st_rec_time > 0 else Station.station_repair_time_ms / 1000.0

    sim_params_sat_rec_time = simulation_params["satellite_recovery_time_sec"]
    simulation_params["satellite_recovery_time_sec"] = sim_params_sat_rec_time if sim_params_sat_rec_time > 0 else Satellite.satellite_repair_time_seconds

    print("Simulation parameters:", simulation_params)
    return simulation_params