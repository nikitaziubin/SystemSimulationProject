import random
import pygame
import math

earth_image = None

WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project Kuiper Simulation") # Caption can stay or change
clock = pygame.time.Clock()

# --- Colors ---
BLACK = (0, 0, 0)
DARK_SPACE = (10, 10, 30)
# --- Restored Original Satellite Colors ---
SATELLITE_BLUE = (0, 100, 180) # Commercial
SATELLITE_GREEN = (0, 150, 80) # Military
# --- End Restored Colors ---
BLINK_RED = (255, 50, 50)
DAMAGED_SATELLITE_COLOR = (100, 100, 100)
DAMAGED_PANEL_COLOR = (80, 80, 80)
OPERATIONAL_PANEL_COLOR = (180, 180, 60)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
STAR_COLOR = (200, 200, 200)
STATION_COLOR = (120, 120, 120)
STATION_SELECTED_COLOR = (200, 200, 200)
COMM_RADIUS_COLOR = (0, 120, 0, 100)
COMM_RADIUS_SELECTED_COLOR = (0, 200, 0, 130)
COMM_LINE_COLOR = (180, 180, 180)
CAPACITY_FULL_COLOR = (255, 0, 0)
CAPACITY_NORMAL_COLOR = (0, 255, 0)
# --- Removed Altitude-Specific Colors ---
# KUIPER_COLOR_590 = (0, 200, 200)
# KUIPER_COLOR_610 = (200, 0, 200)
# KUIPER_COLOR_630 = (200, 200, 0)
# --- End Removed Colors ---


# --- Real World Constants (Unchanged) ---
EARTH_RADIUS_KM = 6371.0
G = 6.67430e-11
EARTH_MASS_KG = 5.97219e24
G_KM = G / (1000.0**3)

# --- Simulation Scale (Using the zoomed value) ---
EARTH_RADIUS_PIXELS = 340 # Keep the zoomed value
SCALE_FACTOR = EARTH_RADIUS_PIXELS / EARTH_RADIUS_KM

# --- Simulation Parameters (Unchanged logic) ---
EARTH_POSITION = (WIDTH // 2, HEIGHT // 2)

# Kuiper Parameters (Still used for altitudes)
KUIPER_ALTITUDES_KM = [590.0, 610.0, 630.0]
# KUIPER_COLORS removed
KUIPER_ORBIT_RADII_PIXELS = [(EARTH_RADIUS_KM + alt) * SCALE_FACTOR for alt in KUIPER_ALTITUDES_KM]

# --- Station Parameters (Unchanged from previous step) ---
STATION_MIN_DISTANCE = 40
MIN_STATION_COMM_RADIUS = 50
MAX_STATION_COMM_RADIUS = 400
STATION_SELECTION_RADIUS = 20
STATION_ALPHA_NORMAL = 180
STATION_ALPHA_SELECTED = 255
STATION_RADIUS_CLICK_CHANGE = 10
STATION_MAX_CAPACITY = 5
STATION_COMM_ANGLE_DEG = 210
STATION_ARC_POLYGON_SEGMENTS = 20
STATION_DAMAGE_PROBABILITY = 0.001
STATION_REPAIR_TIME_MS = 5000
STATION_DATA_LOSS_ON_REPAIR = 2

# --- Damage and Blinking (Unchanged) ---
SATELLITE_DAMAGE_PROBABILITY = 0.0003
BLINK_DURATION_MS = 5000
BLINK_INTERVAL_MS = 250

# --- Stars (Unchanged) ---
STAR_COUNT = 350
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1.5)) for _ in range(STAR_COUNT)]

# --- Utility function get_color_for_altitude REMOVED ---