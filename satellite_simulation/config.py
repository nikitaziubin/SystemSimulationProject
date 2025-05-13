import random
import pygame
import math
import os

EARTH_IMAGE_FILENAME = "earth.jpg"

earth_image = None

WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project Kuiper Simulation")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
DARK_SPACE = (10, 10, 30)
SATELLITE_BLUE = (0, 100, 180)
SATELLITE_GREEN = (0, 150, 80)
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

EARTH_RADIUS_KM = 6371.0
G = 6.67430e-11
EARTH_MASS_KG = 5.97219e24
G_KM = G / (1000.0**3)

EARTH_RADIUS_PIXELS = 340
SCALE_FACTOR = EARTH_RADIUS_PIXELS / EARTH_RADIUS_KM

EARTH_POSITION = (WIDTH // 2, HEIGHT // 2)
KUIPER_ALTITUDES_KM = [590.0, 610.0, 630.0]
KUIPER_ORBIT_RADII_PIXELS = [(EARTH_RADIUS_KM + alt) * SCALE_FACTOR for alt in KUIPER_ALTITUDES_KM]

try:
    script_dir = os.path.dirname(__file__)
    image_path = os.path.join(script_dir, EARTH_IMAGE_FILENAME)

    _raw_earth_image = pygame.image.load(image_path).convert_alpha()
    earth_diameter_pixels = int(EARTH_RADIUS_PIXELS * 2)
    earth_image = pygame.transform.scale(_raw_earth_image, (earth_diameter_pixels, earth_diameter_pixels))
    print(f"Successfully loaded and scaled {EARTH_IMAGE_FILENAME}")
except FileNotFoundError:
    print(f"Warning: Earth image '{EARTH_IMAGE_FILENAME}' not found. Drawing blue circle instead.")
    earth_image = None
except pygame.error as e:
    print(f"Warning: Error loading image '{EARTH_IMAGE_FILENAME}': {e}. Drawing blue circle instead.")
    earth_image = None

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


SATELLITE_DAMAGE_PROBABILITY = 0.0003
BLINK_DURATION_MS = 5000
BLINK_INTERVAL_MS = 250

SIMULATION_SPEED = 1.0

STAR_COUNT = 350
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1.5)) for _ in range(STAR_COUNT)]