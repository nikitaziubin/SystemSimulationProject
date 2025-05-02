import random
import pygame
import math # Added math import

earth_image = None

WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project Kuiper Simulation") # Updated caption
clock = pygame.time.Clock()

# --- Colors (Unchanged) ---
BLACK = (0, 0, 0)
DARK_SPACE = (10, 10, 30)
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
KUIPER_COLOR_590 = (0, 200, 200) # Cyan
KUIPER_COLOR_610 = (200, 0, 200) # Magenta
KUIPER_COLOR_630 = (200, 200, 0) # Yellowish

# --- Real World Constants (Unchanged) ---
EARTH_RADIUS_KM = 6371.0  # Earth's mean radius in kilometers
G = 6.67430e-11  # Gravitational constant in m^3 kg^-1 s^-2
EARTH_MASS_KG = 5.97219e24  # Earth's mass in kg
G_KM = G / (1000.0**3) # G in km^3 kg^-1 s^-2

# --- Simulation Scale ---
# Increase EARTH_RADIUS_PIXELS to "zoom in"
# Original was 150. Let's try 340. Max fitting radius is min(1200/2, 900/2)=450
EARTH_RADIUS_PIXELS = 340 # <<< ZOOM INCREASED HERE
# Calculate scale: pixels per kilometer (this automatically updates)
SCALE_FACTOR = EARTH_RADIUS_PIXELS / EARTH_RADIUS_KM # pixels/km

# --- Simulation Parameters (Unchanged logic) ---
EARTH_POSITION = (WIDTH // 2, HEIGHT // 2)

# Kuiper Parameters (Unchanged logic)
KUIPER_ALTITUDES_KM = [590.0, 610.0, 630.0] # Target altitudes in km
KUIPER_COLORS = [KUIPER_COLOR_590, KUIPER_COLOR_610, KUIPER_COLOR_630]
# Calculate orbital radii in pixels for simulation (this automatically updates)
KUIPER_ORBIT_RADII_PIXELS = [(EARTH_RADIUS_KM + alt) * SCALE_FACTOR for alt in KUIPER_ALTITUDES_KM]
# Print calculated orbit radii in pixels for reference (optional)
# print(f"Calculated Pixel Orbit Radii: {KUIPER_ORBIT_RADII_PIXELS}")
# With EARTH_RADIUS_PIXELS = 340, orbits are approx [368.2, 370.9, 373.5] pixels

# --- Station Parameters ---
STATION_MIN_DISTANCE = 40 # In pixels - keep as is, relative visual spacing
MIN_STATION_COMM_RADIUS = 50  # In pixels - keep minimum visual size
# Adjust max radius relative to new zoomed view. Outermost orbit is ~374px.
MAX_STATION_COMM_RADIUS = 400 # In pixels - Increased slightly to extend beyond orbits
STATION_SELECTION_RADIUS = 20
STATION_ALPHA_NORMAL = 180
STATION_ALPHA_SELECTED = 255
STATION_RADIUS_CLICK_CHANGE = 10
STATION_MAX_CAPACITY = 5
STATION_COMM_ANGLE_DEG = 210
STATION_ARC_POLYGON_SEGMENTS = 20
STATION_DAMAGE_PROBABILITY = 0.001 # Default, can be overridden by popup
STATION_REPAIR_TIME_MS = 5000     # Default, can be overridden by popup
STATION_DATA_LOSS_ON_REPAIR = 2

# --- Damage and Blinking (Unchanged) ---
SATELLITE_DAMAGE_PROBABILITY = 0.0003 # Default, can be overridden by popup
BLINK_DURATION_MS = 5000 # Default, can be overridden by popup (used satellite_repair_time_seconds)
BLINK_INTERVAL_MS = 250

# --- Stars (Unchanged) ---
STAR_COUNT = 350
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1.5)) for _ in range(STAR_COUNT)]

# --- Utility function to get color based on altitude (Unchanged) ---
def get_color_for_altitude(altitude_km):
    if altitude_km == 590.0:
        return KUIPER_COLOR_590
    elif altitude_km == 610.0:
        return KUIPER_COLOR_610
    elif altitude_km == 630.0:
        return KUIPER_COLOR_630
    else:
        return WHITE # Default fallback