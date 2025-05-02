import random
import pygame
import math # Ensure math is imported
from config import * # Imports new constants like G_KM, EARTH_MASS_KG, EARTH_RADIUS_KM, SCALE_FACTOR
import time

JAMMING_PROBABILITY = 0.01 # Keep or adjust as needed
JAMMING_DATA_LOSS_FACTOR = 0.5 # Keep or adjust as needed

class Satellite:
    destroyed_satellites_log = []
    jamming_log = []

    # Defaults, potentially overridden by startsimulation popup
    satellite_damage_probability = SATELLITE_DAMAGE_PROBABILITY
    satellite_repair_time_seconds = BLINK_DURATION_MS / 1000 # Use config constant

    # Modified __init__ to accept altitude and calculate speed
    def __init__(self, altitude_km, name, initial_angle=None):
        self.name = name
        self.altitude_km = altitude_km
        self.orbit_radius_km = EARTH_RADIUS_KM + self.altitude_km

        # Calculate orbital speed in km/s
        # v = sqrt(G * M / r) - ensure units match (km, kg, s)
        self.speed_km_per_sec = math.sqrt(G_KM * EARTH_MASS_KG / self.orbit_radius_km)

        # Calculate orbital period in seconds T = 2 * pi * r / v
        self.period_sec = (2 * math.pi * self.orbit_radius_km) / self.speed_km_per_sec

        # Calculate angular speed in radians per second (omega = v / r or 2*pi / T)
        self.angular_speed_rad_per_sec = 2 * math.pi / self.period_sec

        # Store simulation-specific radius in pixels
        self.orbit_radius_pixels = self.orbit_radius_km * SCALE_FACTOR

        # Assign color based on altitude shell
        self.initial_color = get_color_for_altitude(self.altitude_km)
        self.color = self.initial_color

        # Random initial angle if not provided, or allow specific placement
        if initial_angle is None:
             self.angle = random.uniform(0, 2 * math.pi)
        else:
             self.angle = initial_angle # Radians

        # Calculate initial position based on pixel radius
        self.x = EARTH_POSITION[0] + self.orbit_radius_pixels * math.cos(self.angle)
        self.y = EARTH_POSITION[1] + self.orbit_radius_pixels * math.sin(self.angle)

        self.status = 'operational'
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_on = False
        self.connected_to = None

        # Simplified data amount - could be differentiated later if needed
        self.data_amount = 50.0 # Example starting data in GB
        self.transfer_rate = 0.5 # GB per second (adjust as needed)
        self.transferring = False
        self.destroyed_time = None

        # Burst transfer logic (keep or remove as desired)
        self.is_in_burst = False
        self.burst_transfer_rate = self.transfer_rate * 2
        self.burst_duration_ms = 3000
        self.burst_start_time = None
        self.connected_stations_set = set() # Keep track of unique connections for burst

    # Modified update to use angular speed and delta_time
    def update(self, current_ticks, stations, delta_time_ms): # Expect delta_time in ms
        # Disconnect logic
        if self.connected_to and (self.status != 'operational' or self.connected_to not in stations):
            if self.connected_to in stations:
                self.connected_to.disconnect_satellite(self)
            self.connected_to = None
            self.transferring = False # Stop transferring if disconnected

        if self.status == 'operational':
            # Update angle based on angular speed and time elapsed
            # Ensure speed direction randomness if desired (e.g., on init or based on plane)
            # For simplicity, all move counter-clockwise here. Add direction logic if needed.
            delta_time_sec = delta_time_ms / 1000.0
            self.angle += self.angular_speed_rad_per_sec * delta_time_sec
            self.angle %= (2 * math.pi)

            # Update position based on pixel radius
            self.x = EARTH_POSITION[0] + self.orbit_radius_pixels * math.cos(self.angle)
            self.y = EARTH_POSITION[1] + self.orbit_radius_pixels * math.sin(self.angle)

            # Data Transfer Logic (mostly unchanged, uses delta_time_sec)
            if self.connected_to and self.data_amount > 0:
                self.transferring = True

                # Burst logic (if kept)
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

                # Simulate jamming (if kept)
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
            # Use the class variable for repair time
            if elapsed_blink_time > Satellite.satellite_repair_time_seconds * 1000:
                self.status = 'destroyed'
                self.is_blinking = False
                self.destroyed_time = time.time()
                Satellite.destroyed_satellites_log.append(self)
                print(f"Satellite {self.name} destroyed!")
            else:
                # Blinking visual state
                self.blink_on = (elapsed_blink_time // BLINK_INTERVAL_MS) % 2 == 0

    # Draw method (mostly unchanged, uses self.color)
    def draw(self, surface):
        if self.status == 'destroyed':
            return

        x, y = int(self.x), int(self.y)

        body_radius = 5 # Slightly smaller for potentially more satellites
        panel_length = 10
        panel_width = 2

        current_body_color = self.color # Use the altitude-based color
        if self.status == 'damaging':
            current_body_color = BLINK_RED if self.blink_on else DAMAGED_SATELLITE_COLOR
        elif self.transferring: # Indicate transferring
             # Simple blink effect for transferring
             if pygame.time.get_ticks() // 250 % 2 == 0:
                  current_body_color = WHITE # Blink white when transferring

        pygame.draw.circle(surface, current_body_color, (x, y), body_radius)

        panel_color = OPERATIONAL_PANEL_COLOR
        if self.status == 'damaging':
            panel_color = BLINK_RED if self.blink_on else DAMAGED_PANEL_COLOR

        # Keep panel drawing relative to satellite angle if needed, or simplify
        # Simplified panel drawing (two lines extending radially outward)
        angle_rad = self.angle # Use the satellite's orbital angle
        p1_end_x = x + math.cos(angle_rad + math.pi/4) * (body_radius + panel_length)
        p1_end_y = y + math.sin(angle_rad + math.pi/4) * (body_radius + panel_length)
        p2_end_x = x + math.cos(angle_rad - math.pi/4) * (body_radius + panel_length)
        p2_end_y = y + math.sin(angle_rad - math.pi/4) * (body_radius + panel_length)

        pygame.draw.line(surface, panel_color, (x, y), (int(p1_end_x), int(p1_end_y)), panel_width)
        pygame.draw.line(surface, panel_color, (x, y), (int(p2_end_x), int(p2_end_y)), panel_width)


        # Draw connection line
        if self.connected_to:
            line_color = YELLOW if self.is_in_burst else COMM_LINE_COLOR # Indicate burst with yellow
            pygame.draw.line(surface, line_color, (x, y),
                             (int(self.connected_to.x), int(self.connected_to.y)), 1) # Thinner line

        # Draw info text (Data amount and Name) - adjust position if needed
        if self.status != 'destroyed':
            data_text = f"{int(self.data_amount)}GB"
            data_font = pygame.font.SysFont(None, 16)
            data_surface = data_font.render(data_text, True, WHITE)
            surface.blit(data_surface, (x + body_radius + 2, y - data_surface.get_height() // 2))

            name_font = pygame.font.SysFont(None, 14)
            name_surface = name_font.render(self.name, True, WHITE)
            name_rect = name_surface.get_rect(center=(x, y - body_radius - 8)) # Position above satellite
            surface.blit(name_surface, name_rect)