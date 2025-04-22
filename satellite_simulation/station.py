import pygame
import math
from config import *

class Station:
    _id_counter = 0

    def __init__(self, x, y):
        self.id = Station._id_counter
        Station._id_counter += 1
        self.x = x
        self.y = y
        self.comm_radius = 250
        self.size = 25
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.capacity = STATION_MAX_CAPACITY
        self.connected_satellites = []
        self.received_data = 0.0
        self.max_data_capacity = 500.0 

        self.status = 'operational'
        self.damage_start_time = 0
        self.stored_data = 0.0  

        dx = self.x - EARTH_POSITION[0]
        dy = self.y - EARTH_POSITION[1]
        self.base_angle_rad = math.atan2(dy, dx)

    def receive_data(self, amount):
        if self.status == 'damaged':
            return
        self.received_data = min(self.received_data + amount, self.max_data_capacity)


    def draw(self, screen_surface, is_selected, capacity_font):
        radius_color_tuple = COMM_RADIUS_SELECTED_COLOR if is_selected else COMM_RADIUS_COLOR

        if is_selected:
            radius_color_tuple = (0, 200, 0, 60)
        else:
            radius_color_tuple = (0, 120, 0, 30)   

        radius_color = pygame.Color(*radius_color_tuple) # Includes alpha

        if self.comm_radius > 0:
            radius_surface_size = int(self.comm_radius * 2) + 4
            radius_surface = pygame.Surface((radius_surface_size, radius_surface_size), pygame.SRCALPHA)
            arc_center_x = radius_surface_size // 2
            arc_center_y = radius_surface_size // 2
            center_point_on_surface = (arc_center_x, arc_center_y)

            total_arc_angle_rad = math.radians(STATION_COMM_ANGLE_DEG)
            angle_start_math = self.base_angle_rad - total_arc_angle_rad / 2
            angle_end_math = self.base_angle_rad + total_arc_angle_rad / 2 

            # Calculate points for the polygon
            polygon_points = [center_point_on_surface] 
            num_segments = STATION_ARC_POLYGON_SEGMENTS
            angle_step = total_arc_angle_rad / num_segments

            for i in range(num_segments + 1):
                current_math_angle = angle_start_math + i * angle_step
                px = arc_center_x + self.comm_radius * math.cos(current_math_angle)
                py = arc_center_y + self.comm_radius * math.sin(current_math_angle)
                polygon_points.append((int(px), int(py)))

            if len(polygon_points) >= 3:
                try:
                    pygame.draw.polygon(radius_surface, radius_color, polygon_points)
                except Exception as e:
                    print(f"Warning: Could not draw polygon for station {self.id} - {e}")        
            outline_color = (20, 70, 20)  # Light green dashed line

            for i in range(1, len(polygon_points) - 1):
                if i % 2 == 0: 
                    start = polygon_points[i]
                    end = polygon_points[i + 1]
                    pygame.draw.line(radius_surface, outline_color, start, end, 3)

            arc_blit_pos = (int(self.x - arc_center_x), int(self.y - arc_center_y))
            screen_surface.blit(radius_surface, arc_blit_pos)

        self.surface.fill((0, 0, 0, 0)) 
        body_width, body_height = 10, 10
        body_rect = pygame.Rect((self.size // 2) - body_width // 2, (self.size // 2) - body_height // 2, body_width, body_height)
        if self.status == 'damaged':
            body_color = (180, 60, 60)
        else:
            body_color = STATION_SELECTED_COLOR if is_selected else STATION_COLOR
        pygame.draw.rect(self.surface, body_color, body_rect)
        antenna_pos = (self.size // 2, self.size // 2 - body_height // 2 - 2)
        pygame.draw.circle(self.surface, WHITE, antenna_pos, 3)

        alpha = STATION_ALPHA_SELECTED if is_selected else STATION_ALPHA_NORMAL
        self.surface.set_alpha(alpha)
        blit_pos = (int(self.x - self.size // 2), int(self.y - self.size // 2))
        screen_surface.blit(self.surface, blit_pos)

        # --- Draw Capacity Indicator (same as before) ---
        capacity_text = f"{len(self.connected_satellites)}/{self.capacity}"
        cap_color = CAPACITY_NORMAL_COLOR if len(self.connected_satellites) < self.capacity else CAPACITY_FULL_COLOR
        capacity_surface = capacity_font.render(capacity_text, True, cap_color)

        #data_text = f"{self.stored_data:.1f} GB"
        #data_surface = capacity_font.render(data_text, True, WHITE if self.status == 'operational' else BLINK_RED)
        #screen_surface.blit(data_surface, (blit_pos[0] + self.size // 2 - data_surface.get_width() // 2, blit_pos[1] + self.size + 20))

        capacity_pos = (blit_pos[0] + self.size // 2 - capacity_surface.get_width() // 2, blit_pos[1] + self.size + 2)
        screen_surface.blit(capacity_surface, capacity_pos)
        data_text = f"Data: {int(self.received_data)} GB"
        data_surface = capacity_font.render(data_text, True, WHITE)
        data_pos = (blit_pos[0] + self.size // 2 - data_surface.get_width() // 2, blit_pos[1] + self.size + 30)

        screen_surface.blit(data_surface, data_pos)
    

    def update(self, current_ticks):
        if self.status == 'operational' and random.random() < STATION_DAMAGE_PROBABILITY:
            self.status = 'damaged'
            self.damage_start_time = current_ticks
            self.disconnect_all()
            print(f"Station {self.id} damaged!")

        elif self.status == 'damaged':
            if current_ticks - self.damage_start_time > STATION_REPAIR_TIME_MS:
                self.status = 'operational'
            
                lost_data = self.received_data / STATION_DATA_LOSS_ON_REPAIR
                self.received_data -= lost_data
                print(f"Station {self.id} repaired, lost {lost_data:.1f} GB")


    # --- Other Station methods (is_near, is_satellite_in_range, etc.) remain unchanged ---
    def is_near(self, other_station):
        return math.dist((self.x, self.y), (other_station.x, other_station.y)) < STATION_MIN_DISTANCE

    def is_satellite_in_range(self, satellite):
        if satellite.status != 'operational':
            return False
        distance = math.dist((self.x, self.y), (satellite.x, satellite.y))
        if distance > self.comm_radius:
            return False

        dx_sat = satellite.x - self.x
        dy_sat = satellite.y - self.y
        angle_to_sat = math.atan2(dy_sat, dx_sat)

        arc_angle_rad = math.radians(STATION_COMM_ANGLE_DEG)
        start_angle = self.base_angle_rad - arc_angle_rad / 2
        end_angle = self.base_angle_rad + arc_angle_rad / 2

        def normalize_angle_diff(a1, a2):
            diff = a1 - a2
            while diff <= -math.pi: diff += 2 * math.pi
            while diff > math.pi: diff -= 2 * math.pi
            return diff

        angle_diff_start = normalize_angle_diff(angle_to_sat, start_angle)
        angle_diff_end = normalize_angle_diff(angle_to_sat, end_angle)
        arc_width_check = normalize_angle_diff(end_angle, start_angle)

        if arc_width_check >= 0:
             # Check if angle is within the arc using normalized differences
             return angle_diff_start >= -1e-9 and angle_diff_end <= 1e-9 # Use tolerance for float comparison
        else: # Arc wraps around the -pi/pi boundary
             return angle_diff_start >= -1e-9 or angle_diff_end <= 1e-9

    def can_connect(self):
        return len(self.connected_satellites) < self.capacity

    def connect_satellite(self, satellite):
        if self.status == 'damaged':
            return False

        if self.can_connect() and satellite not in self.connected_satellites and satellite.status == 'operational':
            self.connected_satellites.append(satellite)
            satellite.connected_to = self
            return True
        return False

    def disconnect_satellite(self, satellite):
        if satellite in self.connected_satellites:
            self.connected_satellites.remove(satellite)
            if satellite.connected_to == self:
                satellite.connected_to = None

    def disconnect_all(self):
        for sat in list(self.connected_satellites):
            self.disconnect_satellite(sat)

    def change_radius(self, delta):
        self.comm_radius += delta
        self.comm_radius = max(MIN_STATION_COMM_RADIUS, min(self.comm_radius, MAX_STATION_COMM_RADIUS))