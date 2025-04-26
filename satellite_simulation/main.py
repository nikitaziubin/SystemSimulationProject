import pygame
import random
import time
from config import *
from satellite import *
from station import *
from inputbox import InputBox
from button import Button
from startsimulation import show_simulation_popup, start_simulation
import math
from satellite import Satellite
from station import Station
import json

active_losses = {} 
connection_loss_log = []


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 22)
capacity_font = pygame.font.SysFont(None, 18)
selected_station = None
delta_time = clock.tick(60)

satellites = []
stations = []

simulation_end_time = None  # Global variable to track end time
simulation_running = False

satellite_counter = 1

def create_satellite(sat_type):
    global satellite_counter
    orbit_radius = random.uniform(MIN_ORBIT_RADIUS, MAX_ORBIT_RADIUS)
    if sat_type == 'A':
        speed = random.uniform(MIN_SPEED_A, MAX_SPEED_A)
        color = SATELLITE_BLUE
    elif sat_type == 'B':
        speed = random.uniform(MIN_SPEED_B, MAX_SPEED_B)
        color = SATELLITE_GREEN
    else:
        return
    if random.random() < 0.4:
        speed *= -1
    name = f"S"
    satellite_counter += 1
    satellites.append(Satellite(orbit_radius=orbit_radius, speed=speed, color=color, name=name))
    print(f"Created {name} Type {sat_type} satellite with radius {orbit_radius:.0f}, speed {speed:.4f}")


def delete_selected_station():
    global selected_station
    if selected_station in stations:
        stations.remove(selected_station)
        selected_station.disconnect_all()
        print(f"Deleted Station ID {selected_station.id}")
        selected_station = None
    else:
        print("No station selected to delete.")

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

def on_start_simulation_click():
    global simulation_end_time, simulation_running
    params = show_simulation_popup()
    if params:
        simulation_end_time = start_simulation(satellites, stations, disable_manual_controls, params)
        simulation_running = True

def terminate_simulation():
    global simulation_running, manual_controls_enabled, selected_station, satellites, stations
    print("Simulation was terminated by user.")
    simulation_running = False
    satellites.clear()
    stations.clear()
    selected_station = None
    manual_controls_enabled = True

def stop_simulation():
    global simulation_running, manual_controls_enabled, selected_station, satellites, stations
    simulation_running = False

    generate_report(satellites, stations)

    manual_controls_enabled = True
    satellites.clear()
    stations.clear()
    selected_station = None
    connection_loss_log.clear()
    print("Simulation stopped and report generated.")


def generate_report(satellites, stations):
    total_data = sum(station.received_data for station in stations)
    lost_data = sum(
        (entry[2] if len(entry) > 2 else station.received_data / STATION_DATA_LOSS_ON_REPAIR)
        for station in stations for entry in station.damage_log if entry[1]
    )

    with open("simulation_results.txt", "w", encoding="utf-8") as file:
        report_text = ""

        report_text += "Simulation Report\n"
        report_text += "=====================\n"
        report_text += f"Total Data Transferred to Stations: {total_data:.2f} GB\n"
        report_text += f"Estimated Data Lost: {lost_data:.2f} GB\n"
        report_text += "\n"

        report_text += "Destroyed Satellites:\n"
        for i, sat in enumerate(Satellite.destroyed_satellites_log, start=1):
            name = getattr(sat, "name", "Unknown")
            report_text += f" {i}. {name} Destroyed at {time.ctime(sat.destroyed_time)} | Position: ({sat.x:.1f}, {sat.y:.1f})\n"

        report_text += "\nDamaged Stations Timeline:\n"
        for station in stations:
            for entry in station.damage_log:
                damage_time = time.ctime(entry[0])
                if entry[1]:
                    repair_time = time.ctime(entry[1])
                    data_loss = entry[2] if len(entry) > 2 else station.received_data / STATION_DATA_LOSS_ON_REPAIR
                    report_text += f" Station {station.id}: Damaged at {damage_time}, Repaired at {repair_time}, Lost {data_loss:.2f} GB\n"
                else:
                    report_text += f" Station {station.id}: Damaged at {damage_time}, Not yet repaired\n"

        report_text += "\nConnection Loss Events:\n"
        for i, ev in enumerate(connection_loss_log, start=1):
            start_str = time.ctime(ev['start_time'])
            report_text += f" {i}. {ev['sat']} Station {ev['station']}: Outage started at {start_str}, duration {ev['duration']:.2f} s\n"

        # Finally write all at once
        file.write(report_text)

    print("Report written to simulation_results.txt")




# --- Buttons ---
button1 = Button(20, 20, 250, 40, "Create Satellite Type A (Blue)", lambda: create_satellite('A'))
button2 = Button(20, 70, 250, 40, "Create Satellite Type B (Green)", lambda: create_satellite('B'))
button_delete_station = Button(20, 120, 250, 40, "Delete Selected Station", delete_selected_station)
button_start_simulation = Button(20, 170, 250, 40, "Start Simulation", on_start_simulation_click)
button_terminate_simulation = Button(WIDTH - 250, 60, 200, 40, "Terminate Simulation", None)
button_stop_simulation = Button(WIDTH - 250, 110, 200, 40, "Stop Simulation", None)

button_terminate_simulation.action = terminate_simulation
button_stop_simulation.action = stop_simulation
manual_controls_enabled = True

def disable_manual_controls():
    global manual_controls_enabled
    manual_controls_enabled = False


running = True
while running:
    current_ticks = pygame.time.get_ticks()

    prev_conn = { sat: sat.connected_to for sat in satellites }

    # --- Event Handling (remains unchanged) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            clicked_on_button = (
                button1.is_hovered() or
                button2.is_hovered() or
                button_delete_station.is_hovered() or
                button_start_simulation.is_hovered() or
                button_terminate_simulation.is_hovered() or
                button_stop_simulation.is_hovered()
            )
            station_interacted_with = False

            # Left Click
            if event.button == 1:
                if simulation_running:
                    if button_terminate_simulation.is_hovered():
                        button_terminate_simulation.handle_click()
                    if button_stop_simulation.is_hovered():
                        button_stop_simulation.handle_click()
                if clicked_on_button and manual_controls_enabled:
                    button1.handle_click()
                    button2.handle_click()
                    button_delete_station.handle_click()
                    button_start_simulation.handle_click()
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
    # Prioritize Green Satellites (Type B)
    for sat in satellites:
        if sat.status == 'operational' and not sat.connected_to and sat.color == SATELLITE_GREEN:
            best_station = find_closest_available_station(sat)
            if best_station:
                best_station.connect_satellite(sat)

    # Then connect Blue Satellites (Type A)
    for sat in satellites:
        if sat.status == 'operational' and not sat.connected_to and sat.color == SATELLITE_BLUE:
            best_station = find_closest_available_station(sat)
            if best_station:
                best_station.connect_satellite(sat)

    # ── DETECT CONNECTION OUTAGES ──
    # compare old vs new for each satellite
    for sat in satellites:
        old = prev_conn.get(sat)
        new = sat.connected_to
        # 1) link dropped → start outage
        if old is not None and new is None:
            key = (sat, old)
            if key not in active_losses:
                active_losses[key] = {
                    'start_time': time.time(),
                    'sat_pos': (sat.x, sat.y),
                    'st_pos': (old.x, old.y)
                }
        # 2) re‐connected → end outage & log duration
        elif old is None and new is not None:
            key = (sat, new)
            if key in active_losses:
                info = active_losses.pop(key)
                duration = time.time() - info['start_time']
                connection_loss_log.append({
                    'sat': sat.name,
                    'station': new.id,
                    'start_time': info['start_time'],
                    'duration': duration
                })

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

    # ── DRAW RED LINES FOR ACTIVE OUTAGES ──
    now = time.time()
    for info in active_losses.values():
        # only draw if it’s been less than 1 second since the loss started
        if now - info['start_time'] < 1.0:
            sx, sy = info['sat_pos']
            tx, ty = info['st_pos']
            pygame.draw.line(screen, BLINK_RED,
                            (int(tx), int(ty)),
                            (int(sx), int(sy)), 2)

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
    button_delete_station.draw(screen)
    button_start_simulation.draw(screen)
    if simulation_running:
        button_terminate_simulation.draw(screen)
        button_stop_simulation.draw(screen)


    # Show simulation timer if active
    if simulation_running and simulation_end_time:
        remaining_seconds = max(0, int(simulation_end_time - time.time()))
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        timer_text = f"Time Left: {minutes:02d}:{seconds:02d}"
        timer_surface = info_font.render(timer_text, True, YELLOW)
        screen.blit(timer_surface, (WIDTH - timer_surface.get_width() - 20, 20))

        if remaining_seconds <= 0:
            simulation_running = False
            generate_report(satellites, stations)

            manual_controls_enabled = True
            satellites.clear()
            stations.clear()
            selected_station = None
            connection_loss_log.clear()
            print("Simulation finished and elements cleared.")

    pygame.display.flip()
    clock.tick(60)

for station in stations:
    station.disconnect_all()
pygame.quit()
