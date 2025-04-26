import random
import pygame
import math
from config import *
import time

JAMMING_PROBABILITY = 0.01
JAMMING_DATA_LOSS_FACTOR = 0.5

class Satellite:
    destroyed_satellites_log = []
    jamming_log = []

    def __init__(self, orbit_radius, speed, color, name):
        self.name = name
        self.orbit_radius = orbit_radius
        self.speed = speed
        self.initial_color = color
        self.color = color
        self.angle = random.uniform(0, 2 * math.pi)
        self.status = 'operational'
        self.x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
        self.y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)
        self.is_blinking = False
        self.blink_start_time = 0
        self.blink_on = False
        self.connected_to = None
        if color == SATELLITE_GREEN:
            self.data_amount = 70.0
        elif color == SATELLITE_BLUE:
            self.data_amount = 30.0
        self.transfer_rate = 0.5
        self.transferring = False
        self.destroyed_time = None
        self.is_in_burst = False
        self.burst_transfer_rate = self.transfer_rate * 2
        self.burst_duration_ms = 3000
        self.burst_start_time = None
        self.connected_stations_set = set()

    def update(self, current_ticks, stations, delta_time):
        if self.connected_to and (self.status != 'operational' or self.connected_to not in stations):
            if self.connected_to in stations:
                self.connected_to.disconnect_satellite(self)
            self.connected_to = None

        if self.status == 'operational':
            self.angle += self.speed
            self.angle %= 2 * math.pi
            self.x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
            self.y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)

            if self.connected_to:
                self.transferring = True

                if self.connected_to not in self.connected_stations_set:
                    self.is_in_burst = True
                    self.burst_start_time = current_ticks
                    self.connected_stations_set.add(self.connected_to)

                if self.is_in_burst and (current_ticks - self.burst_start_time <= self.burst_duration_ms):
                    current_transfer_rate = self.burst_transfer_rate
                else:
                    self.is_in_burst = False
                    current_transfer_rate = self.transfer_rate

                transferred = current_transfer_rate * (delta_time / 1000)
                transferred = min(transferred, self.data_amount)

                # --- Simulate jamming ---
                if random.random() < JAMMING_PROBABILITY:
                    jammed_transferred = transferred * JAMMING_DATA_LOSS_FACTOR
                    lost_due_to_jamming = transferred - jammed_transferred
                    Satellite.jamming_log.append((self.name, time.ctime(), lost_due_to_jamming))
                    transferred = jammed_transferred

                self.data_amount -= transferred
                self.connected_to.receive_data(transferred)

                if self.data_amount <= 0:
                    self.connected_to.disconnect_satellite(self)
                    self.connected_to = None
                    self.transferring = False
                else:
                    self.transferring = False

                if random.random() < SATELLITE_DAMAGE_PROBABILITY:
                    self.status = 'damaging'
                    self.is_blinking = True
                    self.blink_start_time = current_ticks
                    if self.connected_to:
                        self.connected_to.disconnect_satellite(self)
                        self.connected_to = None
                    self.transferring = False

        elif self.status == 'damaging':
            elapsed_blink_time = current_ticks - self.blink_start_time
            if elapsed_blink_time > BLINK_DURATION_MS:
                self.status = 'destroyed'
                self.is_blinking = False
                self.destroyed_time = time.time()
                Satellite.destroyed_satellites_log.append(self)
            else:
                self.blink_on = (elapsed_blink_time // BLINK_INTERVAL_MS) % 2 == 0

    def draw(self, surface):
        if self.status == 'destroyed':
            return

        x, y = int(self.x), int(self.y)

        body_radius = 6
        panel_length = 12
        panel_width = 3

        current_body_color = self.initial_color
        if self.status == 'damaging':
            current_body_color = BLINK_RED if self.blink_on else DAMAGED_SATELLITE_COLOR
        if self.status == 'operational':
            if self.transferring:
                current_body_color = BLINK_RED if pygame.time.get_ticks() // 300 % 2 == 0 else self.initial_color
            else:
                current_body_color = self.initial_color

        pygame.draw.circle(surface, current_body_color, (x, y), body_radius)

        panel_color = OPERATIONAL_PANEL_COLOR
        if self.status == 'damaging':
            panel_color = BLINK_RED if self.blink_on else DAMAGED_PANEL_COLOR

        panel_angle_rad = self.angle + math.pi / 2

        p1_start_x = x + math.cos(panel_angle_rad) * body_radius
        p1_start_y = y + math.sin(panel_angle_rad) * body_radius
        p1_end_x = x + math.cos(panel_angle_rad) * (body_radius + panel_length)
        p1_end_y = y + math.sin(panel_angle_rad) * (body_radius + panel_length)

        p2_start_x = x - math.cos(panel_angle_rad) * body_radius
        p2_start_y = y - math.sin(panel_angle_rad) * body_radius
        p2_end_x = x - math.cos(panel_angle_rad) * (body_radius + panel_length)
        p2_end_y = y - math.sin(panel_angle_rad) * (body_radius + panel_length)

        pygame.draw.line(surface, panel_color, (int(p1_start_x), int(p1_start_y)), (int(p1_end_x), int(p1_end_y)), panel_width)
        pygame.draw.line(surface, panel_color, (int(p2_start_x), int(p2_start_y)), (int(p2_end_x), int(p2_end_y)), panel_width)

        if self.connected_to:
            line_color = (255, 255, 0) if self.is_in_burst else COMM_LINE_COLOR
            pygame.draw.line(surface, line_color, (x, y),
                             (int(self.connected_to.x), int(self.connected_to.y)), 2)

        if self.status != 'destroyed':
            data_text = f"{int(self.data_amount)} GB"
            data_surface = pygame.font.SysFont(None, 18).render(data_text, True, WHITE)
            surface.blit(data_surface, (x + 10, y - 10))

            name_font = pygame.font.SysFont(None, 15)
            name_surface = name_font.render(self.name, True, WHITE)
            name_rect = name_surface.get_rect(center=(x, y))
            surface.blit(name_surface, name_rect)