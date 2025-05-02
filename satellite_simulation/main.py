import pygame
import random
import time
from config import * # Imports new constants and Kuiper params
from satellite import Satellite # Updated Satellite class
from station import Station
from inputbox import InputBox
from button import Button
from startsimulation import show_simulation_popup, start_simulation # Updated popup
import math
# Removed duplicate Satellite/Station imports
import json

active_losses = {}
connection_loss_log = []
REPORT_FILENAME = "simulation_report.txt"


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project Kuiper Simulation") # Consistent caption
clock = pygame.time.Clock() # Clock for frame timing
font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 22)
capacity_font = pygame.font.SysFont(None, 18)
selected_station = None
# delta_time = clock.tick(60) # Incorrect: delta_time should be calculated inside the loop

satellites = []
stations = []

simulation_end_time = None
simulation_running = False

satellite_counter = 1 # Keep counter for unique names

# --- Removed create_satellite function - now handled by start_simulation ---

def delete_selected_station():
    global selected_station
    if selected_station in stations:
        stations.remove(selected_station)
        selected_station.disconnect_all()
        print(f"Deleted Station ID {selected_station.id}")
        selected_station = None
    else:
        print("No station selected to delete.")

# --- Add Random Station (Unchanged, uses EARTH_RADIUS_PIXELS) ---
def add_random_station():
    max_attempts = 100
    for _ in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        # Use EARTH_RADIUS_PIXELS for placement
        station_x = EARTH_POSITION[0] + EARTH_RADIUS_PIXELS * math.cos(angle)
        station_y = EARTH_POSITION[1] + EARTH_RADIUS_PIXELS * math.sin(angle)
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

# --- Find Closest Station - Prioritize based on satellite needs? (Optional Enhancement) ---
# Current logic is simple proximity + availability. Keep as is for now.
def find_closest_available_station(satellite):
    best_station = None
    min_dist_sq = float('inf')
    for station in stations:
        # Check if station is operational and satellite is within its comms arc/range
        if station.status == 'operational' and station.can_connect() and station.is_satellite_in_range(satellite):
            dist_sq = (station.x - satellite.x)**2 + (station.y - satellite.y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_station = station
    return best_station

# --- Simulation Start/Stop/Terminate ---
def on_start_simulation_click():
    global simulation_end_time, simulation_running, satellites, stations, satellite_counter, manual_controls_enabled
    global active_losses, connection_loss_log # Ensure globals are accessed

    # Clear previous simulation elements if any
    satellites.clear()
    stations.clear()
    active_losses.clear()
    connection_loss_log.clear()
    satellite_counter = 1
    Station._id_counter = 0 # Reset station ID counter

    params = show_simulation_popup() # Get params from the modified popup
    if params:
        # start_simulation now also populates satellites and stations
        simulation_end_time = start_simulation(satellites, stations, disable_manual_controls, params)
        simulation_running = True
        manual_controls_enabled = False # Disable controls immediately
        print(f"Simulation started with {len(satellites)} satellites and {len(stations)} stations.")
    else:
        # Re-enable controls if popup was cancelled
        manual_controls_enabled = True


def terminate_simulation():
    global simulation_running, manual_controls_enabled, selected_station, satellites, stations
    global active_losses, connection_loss_log
    print("Simulation was terminated by user.")
    simulation_running = False

    # Clear simulation state
    satellites.clear()
    stations.clear()
    selected_station = None
    active_losses.clear()
    connection_loss_log.clear()
    manual_controls_enabled = True # Re-enable controls


def stop_simulation():
    global simulation_running, manual_controls_enabled, selected_station, satellites, stations
    global active_losses, connection_loss_log
    print("Simulation stopped.")
    simulation_running = False

    # Log any active losses before clearing
    now = time.time()
    for (sat, station), info in active_losses.items():
        duration = now - info['start_time']
        connection_loss_log.append({
            'sat': sat.name,
            'station': station.id if station else 'None', # Handle potential None case?
            'start_time': info['start_time'],
            'duration': duration
        })
    active_losses.clear()

    # Generate report before clearing elements
    if satellites or stations: # Only generate if there was a sim
         generate_report(satellites, stations, connection_loss_log) # Pass log

    # Clear simulation state
    satellites.clear()
    stations.clear()
    selected_station = None
    connection_loss_log.clear() # Clear log after reporting
    manual_controls_enabled = True # Re-enable controls


# --- Report Generation (pass connection_loss_log) ---
def generate_report(satellites_list, stations_list, conn_loss_log): # Accept lists and log
    total_data = sum(station.received_data for station in stations_list)
    # Calculate lost data more robustly from damage log
    lost_data_damage = 0
    for station in stations_list:
        for entry in station.damage_log:
            # entry format: [damage_time, repair_time, data_lost_at_repair]
            if len(entry) > 2 and entry[1] is not None: # Check if repaired and loss recorded
                lost_data_damage += entry[2]

    # Destroyed satellites (use the class log directly)
    destroyed_sats_log = Satellite.destroyed_satellites_log
    # Station damage log (already iterated above for data loss)

    report_filename = REPORT_FILENAME
    with open(report_filename, "w", encoding="utf-8") as file:
        report_text = "Simulation Report\n"
        report_text += "=====================\n"
        report_text += f"Simulation End Time: {time.ctime()}\n"
        report_text += f"Total Satellites Simulated: {len(satellites_list) + len(destroyed_sats_log)}\n"
        report_text += f"Total Stations Simulated: {len(stations_list)}\n"
        report_text += f"Total Data Transferred to Stations: {total_data:.2f} GB\n"
        report_text += f"Estimated Data Lost due to Station Repair: {lost_data_damage:.2f} GB\n"
        report_text += "\n"

        report_text += f"Destroyed Satellites ({len(destroyed_sats_log)}):\n"
        if not destroyed_sats_log:
            report_text += "  None\n"
        else:
            for i, sat_info in enumerate(destroyed_sats_log, start=1):
                 # Log now stores satellite object itself
                 name = getattr(sat_info, "name", "Unknown")
                 destroy_time = getattr(sat_info, "destroyed_time", None)
                 pos_x = getattr(sat_info, "x", "N/A")
                 pos_y = getattr(sat_info, "y", "N/A")
                 time_str = time.ctime(destroy_time) if destroy_time else "N/A"
                 report_text += f" {i}. {name} Destroyed at {time_str} | Last Pos: ({pos_x:.1f}, {pos_y:.1f})\n"
        report_text += "\n"


        report_text += "Damaged Stations Timeline:\n"
        any_station_damage = False
        for station in stations_list:
            if station.damage_log:
                any_station_damage = True
                report_text += f" Station {station.id}:\n"
                for entry in station.damage_log:
                    damage_time_str = time.ctime(entry[0])
                    if entry[1]: # Repaired
                        repair_time_str = time.ctime(entry[1])
                        data_loss = entry[2] if len(entry) > 2 else 0.0 # Get recorded loss
                        report_text += f"  - Damaged: {damage_time_str}, Repaired: {repair_time_str}, Lost: {data_loss:.2f} GB\n"
                    else: # Still damaged at end of sim
                        report_text += f"  - Damaged: {damage_time_str}, Not repaired by sim end.\n"
        if not any_station_damage:
             report_text += "  None\n"
        report_text += "\n"


        report_text += f"Connection Loss Events ({len(conn_loss_log)}):\n"
        if not conn_loss_log:
             report_text += "  None\n"
        else:
             # Sort log by start time for clarity
             conn_loss_log.sort(key=lambda x: x['start_time'])
             for i, ev in enumerate(conn_loss_log, start=1):
                 start_str = time.ctime(ev['start_time'])
                 report_text += (f" {i}. Sat: {ev['sat']}, Station: {ev['station']}, "
                                f"Outage Start: {start_str}, Duration: {ev['duration']:.2f} s\n")

        # Finally write all at once
        file.write(report_text)

    print(f"Report written to {report_filename}")
    # Clear logs after reporting
    Satellite.destroyed_satellites_log.clear()
    # Damage logs are part of station objects, cleared when stations are cleared



# --- Buttons ---
# Removed Add Satellite buttons
# button1 = Button(20, 20, 250, 40, "Add commercial satellite (blue)", lambda: create_satellite('A'))
# button2 = Button(20, 70, 250, 40, "Add military satellite (green)", lambda: create_satellite('B'))
button_delete_station = Button(20, 70, 250, 40, "Delete Selected Station", delete_selected_station) # Adjusted Y pos
button_add_random_station = Button(20, 120, 250, 40, "Add Random Station", add_random_station) # New button
button_start_simulation = Button(20, 170, 250, 40, "Configure & Start Sim", on_start_simulation_click) # Renamed, Adjusted Y pos

# Simulation control buttons (position adjusted slightly)
button_terminate_simulation = Button(WIDTH - 270, 70, 250, 40, "Terminate Simulation", terminate_simulation)
button_stop_simulation = Button(WIDTH - 270, 120, 250, 40, "Stop Sim & Gen Report", stop_simulation) # Renamed

# State variable for button enable/disable
manual_controls_enabled = True

def disable_manual_controls():
    global manual_controls_enabled
    manual_controls_enabled = False
    print("Manual controls disabled for simulation.")

# --- Main Loop ---
running = True
while running:
    # Calculate delta_time properly inside the loop (in milliseconds)
    delta_time_ms = clock.tick(60) # Limit FPS and get time since last frame

    current_ticks = pygame.time.get_ticks() # For blinking, damage timers etc.

    # Store previous connection state for loss detection
    prev_conn = {sat: sat.connected_to for sat in satellites if sat.status != 'destroyed'}

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Handle clicks only if not simulating OR if clicking sim control buttons
        is_sim_control_click = False
        if simulation_running:
             if button_terminate_simulation.is_hovered() or button_stop_simulation.is_hovered():
                 is_sim_control_click = True

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # Handle Simulation Control Buttons FIRST if simulation is running
            if simulation_running:
                if button_terminate_simulation.is_hovered():
                    button_terminate_simulation.handle_click()
                    continue # Skip other click handling
                if button_stop_simulation.is_hovered():
                    button_stop_simulation.handle_click()
                    continue # Skip other click handling

            # Handle Manual Control Buttons ONLY if enabled
            if manual_controls_enabled:
                clicked_on_manual_button = False
                if button_delete_station.is_hovered():
                     button_delete_station.handle_click()
                     clicked_on_manual_button = True
                elif button_add_random_station.is_hovered():
                     button_add_random_station.handle_click()
                     clicked_on_manual_button = True
                elif button_start_simulation.is_hovered():
                     button_start_simulation.handle_click() # This will disable controls if successful
                     clicked_on_manual_button = True
                # Add other manual buttons here if needed

                if clicked_on_manual_button:
                    continue # Skip station interaction if a button was clicked

            # --- Station Interaction (Selection, Radius Change, Manual Placement) ---
            # Allow station interaction even during simulation for viewing info? Yes.
            # Allow radius change / placement only if manual controls enabled? Yes.

            station_interacted_with = False
            new_selection = None
            min_dist_sq = STATION_SELECTION_RADIUS**2

            # Station Selection (Always allowed)
            if event.button == 1: # Left Click
                for station in stations:
                    dist_sq = (mouse_x - station.x)**2 + (mouse_y - station.y)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        new_selection = station

                if new_selection:
                    station_interacted_with = True
                    if new_selection == selected_station:
                        # Increase radius only if manual controls enabled
                        if manual_controls_enabled:
                            selected_station.change_radius(STATION_RADIUS_CLICK_CHANGE)
                    else:
                        selected_station = new_selection # Select new station
                elif not is_sim_control_click and not clicked_on_manual_button: # Clicked on empty space
                    selected_station = None

                # Manual Station Placement (Only if manual controls enabled)
                if manual_controls_enabled and not station_interacted_with and not clicked_on_manual_button:
                    # Check if click is near Earth's edge (using pixel radius)
                    dist_to_earth_center = math.dist((mouse_x, mouse_y), EARTH_POSITION)
                    if abs(dist_to_earth_center - EARTH_RADIUS_PIXELS) < 20: # Tolerance
                         # Project click onto Earth's surface
                         if dist_to_earth_center > 0:
                              factor = EARTH_RADIUS_PIXELS / dist_to_earth_center
                              station_x = EARTH_POSITION[0] + (mouse_x - EARTH_POSITION[0]) * factor
                              station_y = EARTH_POSITION[1] + (mouse_y - EARTH_POSITION[1]) * factor
                         else: # Click exactly at center? Place at top.
                              station_x = EARTH_POSITION[0]
                              station_y = EARTH_POSITION[1] - EARTH_RADIUS_PIXELS

                         # Check proximity to other stations
                         can_place = True
                         for existing_station in stations:
                              if math.dist((station_x, station_y), (existing_station.x, existing_station.y)) < STATION_MIN_DISTANCE:
                                   can_place = False
                                   print("Cannot place station: Too close to another station.")
                                   break
                         if can_place:
                              stations.append(Station(station_x, station_y))
                              print(f"Station added manually near ({station_x:.0f}, {station_y:.0f})")
                              station_interacted_with = True # Count as interaction

            elif event.button == 3: # Right Click (Decrease Radius)
                 # Allow radius decrease only if manual controls enabled AND a station is selected
                 if manual_controls_enabled and selected_station:
                     dist_sq_to_selected = (mouse_x - selected_station.x)**2 + (mouse_y - selected_station.y)**2
                     if dist_sq_to_selected < STATION_SELECTION_RADIUS**2:
                         selected_station.change_radius(-STATION_RADIUS_CLICK_CHANGE)
                         station_interacted_with = True


    # --- Update Logic ---
    if simulation_running: # Only update simulation elements if running
        # Update Satellites (pass delta_time_ms)
        # Iterate over a copy for safe removal if needed (though destruction is handled by filtering later)
        for sat in list(satellites):
             sat.update(current_ticks, stations, delta_time_ms)

        # Update Stations
        for station in stations:
             station.update(current_ticks) # Station update might trigger damage/repair

        # Filter out destroyed satellites
        satellites = [sat for sat in satellites if sat.status != 'destroyed']

        # --- Connection Logic ---
        # 1. Disconnect satellites that moved out of range of their connected station
        for station in stations:
             for sat in list(station.connected_satellites): # Iterate copy
                 if not station.is_satellite_in_range(sat) or sat.status != 'operational':
                     station.disconnect_satellite(sat) # This also sets sat.connected_to = None

        # 2. Connect available operational satellites to available operational stations
        # (Consider prioritizing specific satellites/stations later if needed)
        for sat in satellites:
             # Try to connect only if operational and not already connected
             if sat.status == 'operational' and not sat.connected_to:
                  best_station = find_closest_available_station(sat)
                  if best_station:
                       # connect_satellite checks station status, capacity, and adds to list
                       best_station.connect_satellite(sat) # This sets sat.connected_to

        # --- Detect Connection Losses ---
        now = time.time()
        current_conn = {sat: sat.connected_to for sat in satellites if sat.status != 'destroyed'}

        # Check satellites that were previously connected
        for sat, old_station in prev_conn.items():
             if sat not in current_conn or current_conn[sat] is None: # Lost connection
                  if old_station is not None: # Was connected to a valid station
                       key = (sat, old_station)
                       if key not in active_losses:
                            active_losses[key] = {
                                'start_time': now,
                                'sat_pos': (sat.x, sat.y), # Record position at time of loss
                                'st_pos': (old_station.x, old_station.y)
                            }

        # Check satellites that are newly connected (to stop logging loss)
        for sat, new_station in current_conn.items():
             if new_station is not None: # Is now connected
                  # Check if this specific sat-station pair was being logged as a loss
                  key = (sat, new_station)
                  if key in active_losses:
                       info = active_losses.pop(key)
                       duration = now - info['start_time']
                       # Ensure station object is valid before accessing id
                       station_id = new_station.id if new_station else 'Unknown'
                       connection_loss_log.append({
                            'sat': sat.name,
                            'station': station_id,
                            'start_time': info['start_time'],
                            'duration': duration
                       })


    # --- Drawing ---
    screen.fill(DARK_SPACE)
    # Draw Stars
    for x, y, r in stars: pygame.draw.circle(screen, STAR_COLOR, (int(x), int(y)), int(r))

    # Draw Earth (Using pixel radius)
    if earth_image:
        earth_rect = earth_image.get_rect(center=EARTH_POSITION)
        screen.blit(earth_image, earth_rect)
    else:
        pygame.draw.circle(screen, (0, 80, 180), EARTH_POSITION, EARTH_RADIUS_PIXELS) # Use pixel radius

    # Draw Stations
    for station in stations:
        is_selected = (station == selected_station)
        station.draw(screen, is_selected, capacity_font) # Pass font

    # Draw Satellites
    for sat in satellites:
        sat.draw(screen)

    # Draw Active Connection Loss Lines (Briefly)
    if simulation_running:
        now_vis = time.time()
        keys_to_remove = []
        for key, info in active_losses.items():
            # Draw for a short duration after loss starts
            if now_vis - info['start_time'] < 1.5: # Show for 1.5 seconds
                sat_obj, station_obj = key
                # Check if objects still exist (might have been destroyed/deleted)
                if sat_obj in satellites and station_obj in stations:
                     sx, sy = info['sat_pos'] # Use position at time of loss for visual consistency
                     tx, ty = info['st_pos']
                     pygame.draw.line(screen, BLINK_RED, (int(tx), int(ty)), (int(sx), int(sy)), 2)
            # Optional: Remove very old entries from active_losses if they weren't cleared by reconnection
            # else:
            #    keys_to_remove.append(key)
        # for key in keys_to_remove: active_losses.pop(key, None)


    # --- Draw UI ---
    # Info Text (Top Center)
    info_text = ""
    if selected_station:
        conn_count = len(selected_station.connected_satellites)
        cap = selected_station.capacity
        status = selected_station.status.capitalize()
        radius_km = selected_station.comm_radius / SCALE_FACTOR # Show radius in KM
        info_text = (f"Selected Station ID: {selected_station.id} | Status: {status} | "
                     f"Radius: {radius_km:.0f} km | "
                     f"Connections: {conn_count}/{cap}")
        if manual_controls_enabled:
             info_text += " (L/R Click Icon to Change Radius)"
    elif manual_controls_enabled:
         info_text = "Click station icon to select. Click near Earth edge to add manually."
    info_surface = info_font.render(info_text, True, YELLOW if selected_station else WHITE)
    screen.blit(info_surface, (WIDTH // 2 - info_surface.get_width() // 2, 15))

    # Draw Buttons
    if manual_controls_enabled:
        # button1.draw(screen) # Removed
        # button2.draw(screen) # Removed
        button_delete_station.draw(screen)
        button_add_random_station.draw(screen)
        button_start_simulation.draw(screen)

    # Draw Simulation Control buttons if simulation is running or has run
    if simulation_running or simulation_end_time is not None:
        button_terminate_simulation.draw(screen)
        button_stop_simulation.draw(screen)

    # Show simulation timer if active
    if simulation_running and simulation_end_time:
        remaining_seconds = max(0, simulation_end_time - time.time())
        if remaining_seconds <= 0:
            # Simulation time ended, trigger stop action
            stop_simulation() # This will generate report and clear state
        else:
            minutes = int(remaining_seconds // 60)
            seconds = int(remaining_seconds % 60)
            timer_text = f"Sim Time Left: {minutes:02d}:{seconds:02d}"
            timer_surface = info_font.render(timer_text, True, YELLOW)
            screen.blit(timer_surface, (WIDTH - timer_surface.get_width() - 20, 20))


    pygame.display.flip() # Update the full display


# --- Cleanup ---
# Disconnect any remaining connections cleanly on exit
for station in stations:
    station.disconnect_all()
pygame.quit()