import random
import pygame
import math
from config import * # Imports SATELLITE_BLUE, SATELLITE_GREEN etc.
import time

JAMMING_PROBABILITY = 0.01
JAMMING_DATA_LOSS_FACTOR = 0.5

class Satellite:
    destroyed_satellites_log = []
    jamming_log = []

    satellite_damage_probability = SATELLITE_DAMAGE_PROBABILITY
    satellite_repair_time_seconds = BLINK_DURATION_MS / 1000

    # Modified __init__ to accept altitude, name, color
    def __init__(self, altitude_km, name, color, initial_angle=None): # Added color back
        self.name = name
        self.altitude_km = altitude_km
        self.orbit_radius_km = EARTH_RADIUS_KM + self.altitude_km

        # --- Calculations for speed, period, angular speed (Unchanged) ---
        self.speed_km_per_sec = math.sqrt(G_KM * EARTH_MASS_KG / self.orbit_radius_km)
        self.period_sec = (2 * math.pi * self.orbit_radius_km) / self.speed_km_per_sec
        self.angular_speed_rad_per_sec = 2 * math.pi / self.period_sec
        self.orbit_radius_pixels = self.orbit_radius_km * SCALE_FACTOR
        # --- End Calculations ---

        # --- Use passed color ---
        self.initial_color = color # Store the original color
        self.color = color         # Current color starts as the initial color
        # --- End Color ---

        if initial_angle is None:
             self.angle = random.uniform(0, 2 * math.pi)
        else:
             self.angle = initial_angle

        self.x = EARTH_POSITION[0] + self.orbit_radius_pixels * math.cos(self.angle)
        self.y = EARTH_POSITION[1] + self.orbit_radius_pixels * math.sin(self.angle)

        self.status = 'operational'
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_on = False
        self.connected_to = None

        # --- Set data amount based on color (like original logic) ---
        if color == SATELLITE_GREEN: # Military
            self.data_amount = 70.0 # More data
        elif color == SATELLITE_BLUE: # Commercial
            self.data_amount = 30.0 # Less data
        else: # Fallback
             self.data_amount = 50.0
        # --- End Data Amount ---

        self.transfer_rate = 0.5 # GB per second
        self.transferring = False
        self.destroyed_time = None

        self.is_in_burst = False
        self.burst_transfer_rate = self.transfer_rate * 2
        self.burst_duration_ms = 3000
        self.burst_start_time = None
        self.connected_stations_set = set()

    # --- Update method (Unchanged from previous step) ---
    def update(self, current_ticks, stations, delta_time_ms):
        # (Code is identical to the previous version provided)
        # ... [rest of update method] ...
        # Disconnect logic
        if self.connected_to and (self.status != 'operational' or self.connected_to not in stations):
            if self.connected_to in stations:
                self.connected_to.disconnect_satellite(self)
            self.connected_to = None
            self.transferring = False # Stop transferring if disconnected

        if self.status == 'operational':
            # Update angle based on angular speed and time elapsed
            delta_time_sec = delta_time_ms / 1000.0
            self.angle += self.angular_speed_rad_per_sec * delta_time_sec
            self.angle %= (2 * math.pi)

            # Update position based on pixel radius
            self.x = EARTH_POSITION[0] + self.orbit_radius_pixels * math.cos(self.angle)
            self.y = EARTH_POSITION[1] + self.orbit_radius_pixels * math.sin(self.angle)

            # Data Transfer Logic
            if self.connected_to and self.data_amount > 0:
                self.transferring = True

                # Burst logic
                if self.connected_to not in self.connected_stations_set:
                    self.is_in_burst = True
                    self.burst_start_time = current_ticks
                    self.connected_stations_set.add(self.connected_to)

                if self.is_in_burst and (current_ticks - self.burst_start_time <= self.burst_duration_ms):
                    current_transfer_rate = self.burst_transfer_rate
                else:
                    self.is_in_burst = False
                    current_transfer_rate = self.transfer_rate

                # Calculate transferred data based on time
                transferred = current_transfer_rate * delta_time_sec
                transferred = min(transferred, self.data_amount) # Don't transfer more than available

                # Simulate jamming
                if random.random() < JAMMING_PROBABILITY:
                    jammed_transferred = transferred * JAMMING_DATA_LOSS_FACTOR
                    lost_due_to_jamming = transferred - jammed_transferred
                    Satellite.jamming_log.append((self.name, time.ctime(), lost_due_to_jamming))
                    transferred = jammed_transferred

                # Update satellite data and station received data
                if transferred > 0:
                    self.data_amount -= transferred
                    self.connected_to.receive_data(transferred)

                # Check if data depleted or connection lost
                if self.data_amount <= 0:
                    # print(f"Satellite {self.name} data depleted.") # Optional debug
                    self.connected_to.disconnect_satellite(self)
                    self.connected_to = None
                    self.transferring = False

            else: # Not connected or no data left
                 self.transferring = False
                 self.is_in_burst = False # Ensure burst stops if connection drops

            # Damage Check
            if random.random() < Satellite.satellite_damage_probability:
                self.status = 'damaging'
                self.is_blinking = True
                self.blink_start_time = current_ticks
                print(f"Satellite {self.name} damaged!")
                if self.connected_to:
                    self.connected_to.disconnect_satellite(self)
                    self.connected_to = None
                self.transferring = False
                self.is_in_burst = False

        elif self.status == 'damaging':
            # Blinking and destruction logic
            elapsed_blink_time = current_ticks - self.blink_start_time
            if elapsed_blink_time > Satellite.satellite_repair_time_seconds * 1000:
                self.status = 'destroyed'
                self.is_blinking = False
                self.destroyed_time = time.time()
                Satellite.destroyed_satellites_log.append(self)
                print(f"Satellite {self.name} destroyed!")
            else:
                # Blinking visual state
                self.blink_on = (elapsed_blink_time // BLINK_INTERVAL_MS) % 2 == 0


    # --- Draw method (Uses self.color / self.initial_color) ---
    def draw(self, surface):
        # (Code is identical to the previous version provided)
        # ... [rest of draw method] ...
        if self.status == 'destroyed':
            return

        x, y = int(self.x), int(self.y)

        body_radius = 5 # Slightly smaller for potentially more satellites
        panel_length = 10
        panel_width = 2

        # Use initial_color as the base, modify based on state
        current_body_color = self.initial_color
        if self.status == 'damaging':
            current_body_color = BLINK_RED if self.blink_on else DAMAGED_SATELLITE_COLOR
        elif self.transferring: # Indicate transferring by blinking white
             if pygame.time.get_ticks() // 250 % 2 == 0:
                  current_body_color = self.color

        pygame.draw.circle(surface, current_body_color, (x, y), body_radius)

        panel_color = OPERATIONAL_PANEL_COLOR
        if self.status == 'damaging':
            panel_color = BLINK_RED if self.blink_on else DAMAGED_PANEL_COLOR

        # Simplified panel drawing
        angle_rad = self.angle
        p1_end_x = x + math.cos(angle_rad + math.pi/4) * (body_radius + panel_length)
        p1_end_y = y + math.sin(angle_rad + math.pi/4) * (body_radius + panel_length)
        p2_end_x = x + math.cos(angle_rad - math.pi/4) * (body_radius + panel_length)
        p2_end_y = y + math.sin(angle_rad - math.pi/4) * (body_radius + panel_length)

        pygame.draw.line(surface, panel_color, (x, y), (int(p1_end_x), int(p1_end_y)), panel_width)
        pygame.draw.line(surface, panel_color, (x, y), (int(p2_end_x), int(p2_end_y)), panel_width)

        # Draw connection line
        if self.connected_to:
            line_color = YELLOW if self.is_in_burst else COMM_LINE_COLOR
            pygame.draw.line(surface, line_color, (x, y),
                             (int(self.connected_to.x), int(self.connected_to.y)), 1)

        # Draw info text
        if self.status != 'destroyed':
            data_text = f"{int(self.data_amount)}GB"
            data_font = pygame.font.SysFont(None, 16)
            data_surface = data_font.render(data_text, True, WHITE)
            surface.blit(data_surface, (x + body_radius + 2, y - data_surface.get_height() // 2))

            name_font = pygame.font.SysFont(None, 14)
            name_surface = name_font.render(self.name, True, WHITE)
            name_rect = name_surface.get_rect(center=(x, y - body_radius - 8))
            surface.blit(name_surface, name_rect)