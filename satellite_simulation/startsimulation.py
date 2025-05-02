from satellite import Satellite # Updated Satellite class
from station import Station
from config import * # Import new constants etc.
import math
import random
import time
from inputbox import InputBox
from button import Button
import pygame # Ensure pygame is imported

# Initialize pygame if not already done (or ensure it's done in main)
# pygame.init() # Usually done in main.py

# Define constants for the popup window if needed, or use main window vars
POPUP_WIDTH, POPUP_HEIGHT = 500, 600
popup_screen = None # Will be set when popup is shown
popup_clock = pygame.time.Clock()
popup_font = pygame.font.Font(None, 26) # Use a specific font for the popup

# --- start_simulation function ---
# Now populates satellites and stations based on parameters
def start_simulation(satellites_list, stations_list, disable_manual_controls_callback, params):
    global satellite_counter # Access the counter from main.py (make sure it's global there too)

    # Get simulation parameters
    duration_minutes = int(params["duration"])
    duration_seconds = int(params["duration_seconds"])
    num_satellites = int(params["num_satellites"])
    num_stations = int(params["num_stations"])

    # Get optional override parameters for damage/recovery
    station_damage_prob = float(params.get("station_damage_prob", Station.station_damage_probability * 1000)) / 1000.0 # Convert from % input if needed
    station_recovery_sec = float(params.get("station_recovery_time_sec", Station.station_repair_time_ms / 1000.0))
    satellite_damage_prob = float(params.get("satellite_damage_prob", Satellite.satellite_damage_probability * 1000)) / 1000.0
    satellite_recovery_sec = float(params.get("satellite_recovery_time_sec", Satellite.satellite_repair_time_seconds))

    # Apply overrides to class variables (affects all subsequently created instances)
    Station.station_damage_probability = station_damage_prob
    Station.station_repair_time_ms = station_recovery_sec * 1000
    Satellite.satellite_damage_probability = satellite_damage_prob
    Satellite.satellite_repair_time_seconds = satellite_recovery_sec

    # --- Create Stations ---
    stations_list.clear() # Ensure list is empty before adding
    Station._id_counter = 0 # Reset station ID counter
    for i in range(num_stations):
        max_attempts = 50 # Attempts to place without overlap
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
            # Optionally, force placement even if overlapping, or skip
            # stations_list.append(Station(station_x, station_y)) # Force placement example


    # --- Create Satellites ---
    satellites_list.clear() # Ensure list is empty
    satellite_counter = 1 # Reset satellite counter (ensure main.py uses this global)
    altitudes_km = KUIPER_ALTITUDES_KM # Get from config

    for i in range(num_satellites):
        # Distribute satellites somewhat evenly across altitudes
        altitude = altitudes_km[i % len(altitudes_km)]
        # Distribute initial angles somewhat evenly
        initial_angle = (2 * math.pi / num_satellites) * i if num_satellites > 0 else 0
        name = f"KUI-{satellite_counter}"
        satellites_list.append(Satellite(altitude_km=altitude, name=name, initial_angle=initial_angle))
        satellite_counter += 1


    # Disable manual controls in the main script
    disable_manual_controls_callback()

    # Calculate simulation end time
    start_time = time.time()
    simulation_end_time = start_time + (duration_minutes * 60) + duration_seconds

    print(f"--- Simulation Setup ---")
    print(f"Duration: {duration_minutes}m {duration_seconds}s")
    print(f"Satellites: {len(satellites_list)} (Altitudes: {KUIPER_ALTITUDES_KM} km)")
    print(f"Stations: {len(stations_list)}")
    print(f"Station Damage Prob: {Station.station_damage_probability:.4f}, Repair Time: {Station.station_repair_time_ms / 1000.0:.1f}s")
    print(f"Satellite Damage Prob: {Satellite.satellite_damage_probability:.4f}, Repair Time: {Satellite.satellite_repair_time_seconds:.1f}s")
    print(f"------------------------")


    return simulation_end_time


# --- show_simulation_popup function ---
# Modified to ask for number of sats/stations and damage/recovery overrides
def show_simulation_popup():
    global popup_screen # Use global screen variable for the popup

    # Create a dedicated display surface for the popup
    # Use pygame.display.get_surface() to potentially draw over main screen?
    # Or create a new window? Let's try drawing over.
    main_screen = pygame.display.get_surface() # Get the main display surface
    if not main_screen:
         print("Error: Main display surface not found.")
         return None

    # Create a semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Dark semi-transparent background

    # Define popup area
    popup_rect = pygame.Rect((WIDTH - POPUP_WIDTH) // 2, (HEIGHT - POPUP_HEIGHT) // 2, POPUP_WIDTH, POPUP_HEIGHT)
    popup_color = (40, 40, 60) # Dark blue-gray

    # --- Input Boxes ---
    input_boxes = [
        # Simulation Time
        InputBox(popup_rect.x + 50, popup_rect.y + 50, 140, 32, "Duration (min):", "10"),
        InputBox(popup_rect.x + 250, popup_rect.y + 50, 140, 32, "Duration (sec):", "0"),
        # Number of Entities
        InputBox(popup_rect.x + 50, popup_rect.y + 120, 140, 32, "Num Satellites:", "27"), # Default 50
        InputBox(popup_rect.x + 250, popup_rect.y + 120, 140, 32, "Num Stations:", "10"),   # Default 10
        # Optional Overrides (Damage/Recovery) - Use defaults from config if left blank
        InputBox(popup_rect.x + 50, popup_rect.y + 220, 200, 32, "Station Recover Time (s):", f"{Station.station_repair_time_ms / 1000.0:.1f}", is_float=True),
        InputBox(popup_rect.x + 50, popup_rect.y + 280, 200, 32, "Station Damage Prob (%):", f"{Station.station_damage_probability * 100:.2f}", is_float=True), # Show default %
        InputBox(popup_rect.x + 50, popup_rect.y + 340, 200, 32, "Satellite Recover Time (s):", f"{Satellite.satellite_repair_time_seconds:.1f}", is_float=True),
        InputBox(popup_rect.x + 50, popup_rect.y + 400, 200, 32, "Satellite Damage Prob (%):", f"{Satellite.satellite_damage_probability * 100:.2f}", is_float=True), # Show default %
    ]

    # --- Removed custom satellite config ---

    confirmed = False
    cancelled = False

    def confirm():
        nonlocal confirmed
        # Basic validation (ensure numbers are entered)
        try:
             int(input_boxes[0].get_value())
             int(input_boxes[1].get_value())
             int(input_boxes[2].get_value())
             int(input_boxes[3].get_value())
             # Float conversion will handle empty strings via InputBox.get_value()
             confirmed = True
        except ValueError:
             print("Invalid input. Please enter numbers for duration, satellites, and stations.")


    def cancel():
        nonlocal cancelled
        cancelled = True

    # Buttons relative to popup rect
    ok_button = Button(popup_rect.centerx - 150, popup_rect.bottom - 70, 120, 40, "Start Sim", confirm)
    back_button = Button(popup_rect.centerx + 30, popup_rect.bottom - 70, 120, 40, "Cancel", cancel)

    popup_running = True
    while popup_running:

        # Draw previous screen content as background? No, draw overlay.
        main_screen.blit(overlay, (0, 0))

        # Draw popup background
        pygame.draw.rect(main_screen, popup_color, popup_rect, border_radius=10)
        pygame.draw.rect(main_screen, WHITE, popup_rect, width=2, border_radius=10) # Border


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # Pass events to buttons first
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.is_hovered():
                    ok_button.handle_click() # Calls confirm()
                    if confirmed: # Only exit if confirm logic passed validation
                         popup_running = False
                elif back_button.is_hovered():
                    back_button.handle_click() # Calls cancel()
                    popup_running = False # Always exit on cancel

            # Pass events to input boxes
            for box in input_boxes:
                box.handle_event(event)

        # Draw elements onto the main screen within the popup area
        title_surf = popup_font.render("Simulation Configuration", True, WHITE)
        main_screen.blit(title_surf, (popup_rect.centerx - title_surf.get_width() // 2, popup_rect.y + 10))

        for box in input_boxes:
            box.draw(main_screen) # Draw directly onto the main screen

        ok_button.draw(main_screen)
        back_button.draw(main_screen)

        pygame.display.flip() # Update the display to show the popup
        popup_clock.tick(30) # Control popup frame rate

    if cancelled:
        return None # Indicate cancellation to main loop

    # Collect parameters if confirmed
    simulation_params = {
        "duration": input_boxes[0].get_value(),
        "duration_seconds": input_boxes[1].get_value(),
        "num_satellites": input_boxes[2].get_value(),
        "num_stations": input_boxes[3].get_value(),
        # Pass overrides - use get_value which returns 0 or 0.0 for empty/invalid
        "station_recovery_time_sec": input_boxes[4].get_value(),
        "station_damage_prob": input_boxes[5].get_value(), # Input is %
        "satellite_recovery_time_sec": input_boxes[6].get_value(),
        "satellite_damage_prob": input_boxes[7].get_value(), # Input is %
    }

    # Convert probabilities from % to decimal, handling 0 case from empty input
    sim_params_st_dmg_prob = simulation_params["station_damage_prob"]
    simulation_params["station_damage_prob"] = sim_params_st_dmg_prob / 100.0 if sim_params_st_dmg_prob else Station.station_damage_probability

    sim_params_sat_dmg_prob = simulation_params["satellite_damage_prob"]
    simulation_params["satellite_damage_prob"] = sim_params_sat_dmg_prob / 100.0 if sim_params_sat_dmg_prob else Satellite.satellite_damage_probability

    # Handle 0 recovery time for stations (use default)
    sim_params_st_rec_time = simulation_params["station_recovery_time_sec"]
    simulation_params["station_recovery_time_sec"] = sim_params_st_rec_time if sim_params_st_rec_time > 0 else Station.station_repair_time_ms / 1000.0

    # Handle 0 recovery time for satellites (use default)
    sim_params_sat_rec_time = simulation_params["satellite_recovery_time_sec"]
    simulation_params["satellite_recovery_time_sec"] = sim_params_sat_rec_time if sim_params_sat_rec_time > 0 else Satellite.satellite_repair_time_seconds

    print("Simulation parameters:", simulation_params)
    return simulation_params

# Removed SatelliteConfig class as custom satellite definition is removed
# class SatelliteConfig:
#     ...