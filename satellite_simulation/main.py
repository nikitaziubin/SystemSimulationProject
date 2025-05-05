import pygame
import random
import time
# Import config directly to modify SIMULATION_SPEED
import config
from satellite import Satellite
from station import Station
from inputbox import InputBox
from button import Button
# --- Import the new Slider class ---
from slider import Slider
# --- End Import ---
from startsimulation import show_simulation_popup, start_simulation
import math


import textwrap
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# --- Globals (mostly unchanged) ---
active_losses = {}
connection_loss_log = []
REPORT_FILENAME = f"simulation_report_{time.strftime('%Y%m%d_%H%M%S')}.txt" # Unique name

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("Project Kuiper Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 22)
capacity_font = pygame.font.SysFont(None, 18)
selected_station = None

satellites = []
stations = []

simulation_running = False
total_simulation_duration_ms = 0.0
elapsed_simulation_time_ms = 0.0

satellite_counter = 1

# --- delete_selected_station (Unchanged) ---
def delete_selected_station():
    global selected_station
    if selected_station in stations:
        stations.remove(selected_station)
        selected_station.disconnect_all()
        print(f"Deleted Station ID {selected_station.id}")
        selected_station = None
    else:
        print("No station selected to delete.")

# --- add_random_station (Unchanged) ---
def add_random_station():
    max_attempts = 100
    for _ in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        station_x = config.EARTH_POSITION[0] + config.EARTH_RADIUS_PIXELS * math.cos(angle)
        station_y = config.EARTH_POSITION[1] + config.EARTH_RADIUS_PIXELS * math.sin(angle)
        can_place = True
        for existing_station in stations:
            if math.dist((station_x, station_y), (existing_station.x, existing_station.y)) < config.STATION_MIN_DISTANCE:
                can_place = False
                break
        if can_place:
            stations.append(Station(station_x, station_y))
            print(f"Random station added at angle {math.degrees(angle):.1f} deg")
            return
    print("Could not find a free spot for a random station after multiple attempts.")

# --- find_closest_available_station (Unchanged) ---
def find_closest_available_station(satellite):
    best_station = None
    min_dist_sq = float('inf')
    for station in stations:
        if station.status == 'operational' and station.can_connect() and station.is_satellite_in_range(satellite):
            dist_sq = (station.x - satellite.x)**2 + (station.y - satellite.y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_station = station
    return best_station

# --- set_simulation_speed function (Simplified) ---
def set_simulation_speed(factor):
    # Ensure factor is float and within reasonable bounds if needed
    new_speed = max(1.0, float(factor)) # Example: ensure speed is at least 1x
    if new_speed != config.SIMULATION_SPEED:
        config.SIMULATION_SPEED = new_speed
        # Optional: Print only when it changes
        # print(f"Simulation speed set to {config.SIMULATION_SPEED:.1f}x")
# --- End set_simulation_speed function ---


# --- on_start_simulation_click (Reset slider value) ---
def on_start_simulation_click():
    global simulation_running, satellites, stations, satellite_counter, manual_controls_enabled
    global active_losses, connection_loss_log
    global total_simulation_duration_ms, elapsed_simulation_time_ms

    satellites.clear()
    stations.clear()
    active_losses.clear()
    connection_loss_log.clear()
    satellite_counter = 1
    Station._id_counter = 0
    elapsed_simulation_time_ms = 0.0
    config.SIMULATION_SPEED = 1.0 # Reset speed factor
    speed_slider.set_value(1.0) # Reset slider visual and internal value

    params = show_simulation_popup()
    if params:
        duration_minutes = int(params["duration"])
        duration_seconds = int(params["duration_seconds"])
        total_simulation_duration_ms = (duration_minutes * 60 + duration_seconds) * 1000.0

        start_simulation(satellites, stations, disable_manual_controls, params)

        simulation_running = True
        manual_controls_enabled = False
        print(f"Simulation started with {len(satellites)} satellites and {len(stations)} stations.")
        print(f"Total simulation duration: {total_simulation_duration_ms / 1000.0:.1f} seconds.")
    else:
        manual_controls_enabled = True
        total_simulation_duration_ms = 0.0


# --- terminate_simulation (Reset slider value) ---
def terminate_simulation():
    global simulation_running, manual_controls_enabled, selected_station, satellites, stations
    global active_losses, connection_loss_log, elapsed_simulation_time_ms
    print("Simulation was terminated by user.")
    simulation_running = False

    satellites.clear()
    stations.clear()
    selected_station = None
    active_losses.clear()
    connection_loss_log.clear()
    elapsed_simulation_time_ms = 0.0
    manual_controls_enabled = True
    config.SIMULATION_SPEED = 1.0 # Reset speed factor
    speed_slider.set_value(1.0) # Reset slider


# --- stop_simulation (Reset slider value) ---
def stop_simulation():
    global simulation_running, manual_controls_enabled, selected_station, satellites, stations
    global active_losses, connection_loss_log, elapsed_simulation_time_ms
    print("Simulation stopped.")
    simulation_running = False

    now = time.time()
    for (sat, station), info in active_losses.items():
        duration = now - info['start_time']
        connection_loss_log.append({
            'sat': sat.name,
            'station': station.id if station else 'None',
            'start_time': info['start_time'],
            'duration': duration
        })
    active_losses.clear()

    if satellites or stations:
         generate_report(satellites, stations, connection_loss_log, elapsed_simulation_time_ms)

    satellites.clear()
    stations.clear()
    selected_station = None
    connection_loss_log.clear()
    elapsed_simulation_time_ms = 0.0
    manual_controls_enabled = True
    config.SIMULATION_SPEED = 1.0 # Reset speed factor
    speed_slider.set_value(1.0) # Reset slider

# --- generate_report (Unchanged) ---
def generate_report(satellites_list, stations_list, conn_loss_log, final_elapsed_sim_time_ms):
    # ——— Build the text report ———
    total_data = sum(station.received_data for station in stations_list)
    lost_data_damage = 0
    for station in stations_list:
        for entry in station.damage_log:
            if len(entry) > 2 and entry[1] is not None:
                lost_data_damage += entry[2]
    destroyed_sats_log = Satellite.destroyed_satellites_log

    report_txt = []
    report_txt.append("Simulation Report")
    report_txt.append("=====================")
    report_txt.append(f"Report Generated At: {time.ctime()}")
    # Simulation time formatting
    sim_time_sec = final_elapsed_sim_time_ms / 1000.0
    sim_min = int(sim_time_sec // 60)
    sim_sec = sim_time_sec % 60
    report_txt.append(f"Total Simulation Time Elapsed: {sim_min}m {sim_sec:.1f}s")
    report_txt.append(f"Final Simulation Speed: {config.SIMULATION_SPEED:.1f}x")
    report_txt.append(f"Total Satellites Simulated: {len(satellites_list) + len(destroyed_sats_log)}")
    report_txt.append(f"Total Stations Simulated: {len(stations_list)}")
    report_txt.append(f"Total Data Transferred to Stations: {total_data:.2f} GB")
    report_txt.append(f"Estimated Data Lost due to Station Repair: {lost_data_damage:.2f} GB")
    report_txt.append("")

    # Destroyed satellites
    report_txt.append(f"Destroyed Satellites ({len(destroyed_sats_log)}):")
    if not destroyed_sats_log:
        report_txt.append("  None")
    else:
        for i, sat_info in enumerate(destroyed_sats_log, start=1):
            name = getattr(sat_info, "name", "Unknown")
            destroy_time = getattr(sat_info, "destroyed_time", None)
            pos_x = getattr(sat_info, "x", "N/A")
            pos_y = getattr(sat_info, "y", "N/A")
            time_str = time.ctime(destroy_time) if destroy_time else "N/A"
            report_txt.append(
                f" {i}. {name} Destroyed at {time_str} | Last Pos: ({pos_x:.1f}, {pos_y:.1f})"
            )
    report_txt.append("")

    # Damaged stations
    report_txt.append("Damaged Stations Timeline:")
    any_damage = False
    for station in stations_list:
        if station.damage_log:
            any_damage = True
            report_txt.append(f" Station {station.id}:")
            for entry in station.damage_log:
                dmg_time = time.ctime(entry[0])
                if entry[1]:
                    rep_time = time.ctime(entry[1])
                    loss = entry[2] if len(entry) > 2 else 0.0
                    report_txt.append(f"  - Damaged: {dmg_time}, Repaired: {rep_time}, Lost: {loss:.2f} GB")
                else:
                    report_txt.append(f"  - Damaged: {dmg_time}, Not repaired by sim end.")
    if not any_damage:
        report_txt.append("  None")
    report_txt.append("")

    # Connection loss events
    report_txt.append(f"Connection Loss Events ({len(conn_loss_log)}):")
    if not conn_loss_log:
        report_txt.append("  None")
    else:
        conn_loss_log.sort(key=lambda x: x["start_time"])
        for i, ev in enumerate(conn_loss_log, start=1):
            start_str = time.ctime(ev["start_time"])
            report_txt.append(
                f" {i}. Sat: {ev['sat']}, Station: {ev['station']}, "
                f"Outage Start: {start_str}, Duration: {ev['duration']:.2f} s"
            )

    # Save text report
    txt_filename = "simulation_report.txt"
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report_txt))
    print(f"Text report written to {txt_filename}")

    # ——— Convert to PDF ———
    pdf_filename = "simulation_report.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=LETTER)
    width, height = LETTER
    margin = 40
    line_h = 14
    max_w = width - 2 * margin

    y = height - margin
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "Simulation Report")
    y -= 2 * line_h

    # Body
    c.setFont("Helvetica", 12)
    for line in report_txt:
        # Wrap text
        for sub in textwrap.wrap(line, width=int(max_w / 7)) or [""]:
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 12)
            c.drawString(margin, y, sub)
            y -= line_h

    c.save()
    print(f"PDF report written to {pdf_filename}")

    # Clear destroyed log
    Satellite.destroyed_satellites_log.clear()

# --- disable_manual_controls (Unchanged) ---
def disable_manual_controls():
    global manual_controls_enabled
    manual_controls_enabled = False
    print("Manual controls disabled for simulation.")

# --- Buttons ---
# Manual Controls (Unchanged)
button_delete_station = Button(20, 70, 250, 40, "Delete Selected Station", delete_selected_station)
button_add_random_station = Button(20, 120, 250, 40, "Add Random Station", add_random_station)
button_start_simulation = Button(20, 170, 250, 40, "Configure & Start Sim", on_start_simulation_click)

# Simulation Controls (Unchanged)
sim_ctrl_x = config.WIDTH - 270
button_terminate_simulation = Button(sim_ctrl_x, 70, 250, 40, "Terminate Simulation", terminate_simulation)
button_stop_simulation = Button(sim_ctrl_x, 120, 250, 40, "Stop Sim & Gen Report", stop_simulation)

# --- Remove Speed Buttons ---
# button_speed_1x = ...
# button_speed_2x = ...
# button_speed_4x = ...
# button_speed_8x = ...
# speed_buttons = [...]
# --- End Remove Speed Buttons ---

# --- ADD Speed Slider ---
speed_slider_y = 180 # Position below stop button
speed_slider_w = 250 # Approx width of old buttons
speed_slider_h = 20  # Height of slider track area
speed_slider = Slider(sim_ctrl_x, speed_slider_y, speed_slider_w, speed_slider_h,
                      min_val=1.0, max_val=64.0, initial_val=1.0, label="Speed: ")
# --- End Speed Slider ---

# State variable for button enable/disable
manual_controls_enabled = True

# --- Main Loop ---
running = True
while running:
    delta_time_ms = clock.tick(60)
    current_ticks = pygame.time.get_ticks() # For real-time events like station repair

    # --- Update Speed from Slider ---
    # Do this *before* calculating effective delta time if the slider might change it
    if simulation_running:
        new_speed = speed_slider.get_value()
        # Optional: Set speed only if it changed significantly to avoid float comparison issues
        if abs(new_speed - config.SIMULATION_SPEED) > 0.01:
             set_simulation_speed(new_speed)
             # print(f"Slider value changed, new speed: {config.SIMULATION_SPEED:.1f}x") # Debug
    # --- End Update Speed ---

    # Calculate effective simulation time elapsed this frame
    effective_delta_time_ms = delta_time_ms * config.SIMULATION_SPEED

    # Update total elapsed simulation time
    if simulation_running:
        elapsed_simulation_time_ms += effective_delta_time_ms

    # Store previous connection state (Unchanged)
    prev_conn = {sat: sat.connected_to for sat in satellites if sat.status != 'destroyed'}

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Handle Slider Event FIRST if sim running ---
        if simulation_running:
            speed_slider.handle_event(event)
        # --- End Slider Event Handling ---

        # Mouse Button Down Logic (Removed speed button checks)
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Prevent interaction below if slider handled it
            # Note: Slider handle_event doesn't return True/False, so we rely on
            #       checking if the mouse was over the slider *before* handling other clicks.
            #       This isn't perfect but often works. A better Slider class might return consumed status.
            mouse_x, mouse_y = event.pos
            slider_hover = speed_slider.rect.collidepoint(mouse_x, mouse_y) if simulation_running else False

            clicked_on_manual_button = False
            clicked_on_sim_control = False


            # Handle Simulation Control Buttons (Stop/Terminate)
            if simulation_running and not slider_hover: # Don't handle if click was on slider
                if button_terminate_simulation.is_hovered():
                    button_terminate_simulation.handle_click()
                    clicked_on_sim_control = True
                elif button_stop_simulation.is_hovered():
                    button_stop_simulation.handle_click()
                    clicked_on_sim_control = True

                if clicked_on_sim_control: continue

            # Handle Manual Control Buttons
            if manual_controls_enabled and not slider_hover:
                if button_delete_station.is_hovered():
                     button_delete_station.handle_click()
                     clicked_on_manual_button = True
                elif button_add_random_station.is_hovered():
                     button_add_random_station.handle_click()
                     clicked_on_manual_button = True
                elif button_start_simulation.is_hovered():
                     button_start_simulation.handle_click()
                     clicked_on_manual_button = True

                if clicked_on_manual_button: continue

            # Station Interaction (only if not clicking slider or buttons)
            if not slider_hover and not clicked_on_manual_button and not clicked_on_sim_control:
                station_interacted_with = False
                new_selection = None
                min_dist_sq = config.STATION_SELECTION_RADIUS**2

                # Left Click
                if event.button == 1:
                    for station in stations:
                        dist_sq = (mouse_x - station.x)**2 + (mouse_y - station.y)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            new_selection = station
                    if new_selection:
                        station_interacted_with = True
                        if new_selection == selected_station:
                            if manual_controls_enabled: selected_station.change_radius(config.STATION_RADIUS_CLICK_CHANGE)
                        else: selected_station = new_selection
                    else: selected_station = None

                    # Manual Station Placement
                    if manual_controls_enabled and not station_interacted_with:
                        dist_to_earth_center = math.dist((mouse_x, mouse_y), config.EARTH_POSITION)
                        if abs(dist_to_earth_center - config.EARTH_RADIUS_PIXELS) < 20:
                             # ... (Placement logic unchanged) ...
                             if dist_to_earth_center > 0:
                                  factor = config.EARTH_RADIUS_PIXELS / dist_to_earth_center
                                  station_x = config.EARTH_POSITION[0] + (mouse_x - config.EARTH_POSITION[0]) * factor
                                  station_y = config.EARTH_POSITION[1] + (mouse_y - config.EARTH_POSITION[1]) * factor
                             else:
                                  station_x = config.EARTH_POSITION[0]; station_y = config.EARTH_POSITION[1] - config.EARTH_RADIUS_PIXELS
                             can_place = True
                             for existing_station in stations:
                                  if math.dist((station_x, station_y), (existing_station.x, existing_station.y)) < config.STATION_MIN_DISTANCE:
                                       can_place = False; print("Cannot place station: Too close to another station."); break
                             if can_place: stations.append(Station(station_x, station_y)); print(f"Station added manually near ({station_x:.0f}, {station_y:.0f})"); station_interacted_with = True

                # Right Click
                elif event.button == 3:
                     if manual_controls_enabled and selected_station:
                         dist_sq_to_selected = (mouse_x - selected_station.x)**2 + (mouse_y - selected_station.y)**2
                         if dist_sq_to_selected < config.STATION_SELECTION_RADIUS**2:
                             selected_station.change_radius(-config.STATION_RADIUS_CLICK_CHANGE); station_interacted_with = True


    # --- Update Logic (Unchanged) ---
    if simulation_running:
        for sat in list(satellites):
             sat.update(current_ticks, stations, effective_delta_time_ms) # Pass effective time
        for station in stations:
             station.update(current_ticks) # Pass real pygame ticks

        satellites = [sat for sat in satellites if sat.status != 'destroyed']

        # Connection Logic (Unchanged)
        for station in stations:
             for sat in list(station.connected_satellites):
                 if not station.is_satellite_in_range(sat) or sat.status != 'operational':
                     station.disconnect_satellite(sat)
        for sat in satellites:
             if sat.status == 'operational' and not sat.connected_to:
                  best_station = find_closest_available_station(sat)
                  if best_station: best_station.connect_satellite(sat)

        # Detect Connection Losses (Unchanged)
        now_real = time.time()
        current_conn = {sat: sat.connected_to for sat in satellites if sat.status != 'destroyed'}
        for sat, old_station in prev_conn.items():
             if sat not in current_conn or current_conn[sat] is None:
                  if old_station is not None:
                       key = (sat, old_station)
                       if key not in active_losses: active_losses[key] = {'start_time': now_real, 'sat_pos': (sat.x, sat.y), 'st_pos': (old_station.x, old_station.y)}
        for sat, new_station in current_conn.items():
             if new_station is not None:
                  key = (sat, new_station)
                  if key in active_losses:
                       info = active_losses.pop(key); duration = now_real - info['start_time']; station_id = new_station.id if new_station else 'Unknown'
                       connection_loss_log.append({'sat': sat.name, 'station': station_id, 'start_time': info['start_time'], 'duration': duration})


    # --- Drawing ---
    screen.fill(config.DARK_SPACE)
    # Draw Stars, Earth, Stations, Satellites (Unchanged)
    for x, y, r in config.stars: pygame.draw.circle(screen, config.STAR_COLOR, (int(x), int(y)), int(r))
    if config.earth_image:
        screen.blit(config.earth_image, config.earth_image.get_rect(center=config.EARTH_POSITION))
    else:
        pygame.draw.circle(screen, (0, 80, 180), config.EARTH_POSITION, config.EARTH_RADIUS_PIXELS)
    for station in stations: station.draw(screen, (station == selected_station), capacity_font)
    for sat in satellites: sat.draw(screen)

    # Draw Active Connection Loss Lines (Unchanged)
    if simulation_running:
        now_vis_real = time.time()
        for key, info in active_losses.items():
            if now_vis_real - info['start_time'] < 1.5:
                sat_obj, station_obj = key
                if sat_obj in satellites and station_obj in stations:
                     sx, sy = info['sat_pos']; tx, ty = info['st_pos']
                     pygame.draw.line(screen, config.BLINK_RED, (int(tx), int(ty)), (int(sx), int(sy)), 2)

    # --- Draw UI ---
    # Info Text (Unchanged)
    info_text = ""
    # ... (info text generation unchanged) ...
    if selected_station:
        conn_count = len(selected_station.connected_satellites); cap = selected_station.capacity; status = selected_station.status.capitalize()
        radius_km = selected_station.comm_radius / config.SCALE_FACTOR
        info_text = (f"Selected Station ID: {selected_station.id} | Status: {status} | Radius: {radius_km:.0f} km | Connections: {conn_count}/{cap}")
        if manual_controls_enabled: info_text += " (L/R Click Icon to Change Radius)"
    elif manual_controls_enabled: info_text = "Click station icon to select. Click near Earth edge to add manually."
    info_surface = info_font.render(info_text, True, config.YELLOW if selected_station else config.WHITE)
    screen.blit(info_surface, (config.WIDTH // 2 - info_surface.get_width() // 2, 15))

    # Draw Manual Buttons
    if manual_controls_enabled:
        button_delete_station.draw(screen)
        button_add_random_station.draw(screen)
        button_start_simulation.draw(screen)

    # Draw Simulation Control buttons and Slider
    if simulation_running or not manual_controls_enabled:
        button_terminate_simulation.draw(screen)
        button_stop_simulation.draw(screen)
        # --- Draw Slider instead of buttons ---
        speed_slider.draw(screen)
        # --- End Draw Slider ---


    # Show simulation timer (Using elapsed sim time)
    if simulation_running:
        remaining_simulation_ms = max(0, total_simulation_duration_ms - elapsed_simulation_time_ms)
        if remaining_simulation_ms <= 0:
            stop_simulation() # Sim time ended
        else:
            remaining_total_seconds = remaining_simulation_ms / 1000.0
            minutes = int(remaining_total_seconds // 60)
            seconds = int(remaining_total_seconds % 60)
            # Show current speed from config, not slider directly, as slider might be mid-drag
            timer_text = f"Sim Time Left: {minutes:02d}:{seconds:02d} ({config.SIMULATION_SPEED:.1f}x)"
            timer_surface = info_font.render(timer_text, True, config.YELLOW)
            screen.blit(timer_surface, (config.WIDTH - timer_surface.get_width() - 20, 20))


    pygame.display.flip()

# --- Cleanup ---
for station in stations:
    station.disconnect_all()
pygame.quit()