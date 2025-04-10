import pygame # type: ignore
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Satellite Orbit Simulation")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
EARTH_BLUE = (0, 102, 204)
SATELLITE_RED = (255, 0, 0)
SATELLITE_GREEN = (0, 255, 0)
WHITE = (255, 255, 255)

EARTH_RADIUS = 40
EARTH_POSITION = (WIDTH // 2, HEIGHT // 2)

class Satellite:
    def __init__(self, orbit_radius, speed, color):
        self.orbit_radius = orbit_radius
        self.speed = speed
        self.color = color
        self.angle = random.uniform(0, 2 * math.pi)

    def update(self):
        self.angle += self.speed
        self.angle %= 2 * math.pi

    def draw(self, surface):
        x = EARTH_POSITION[0] + self.orbit_radius * math.cos(self.angle)
        y = EARTH_POSITION[1] + self.orbit_radius * math.sin(self.angle)
        pygame.draw.circle(surface, self.color, (int(x), int(y)), 6)

satellites = []

running = True
font = pygame.font.SysFont(None, 24)

def draw_ui():
    text1 = font.render("Press 1 to create Satellite Type A (Red)", True, WHITE)
    text2 = font.render("Press 2 to create Satellite Type B (Green)", True, WHITE)
    screen.blit(text1, (10, 10))
    screen.blit(text2, (10, 35))

while running:
    clock.tick(60)
    screen.fill(BLACK)

    pygame.draw.circle(screen, EARTH_BLUE, EARTH_POSITION, EARTH_RADIUS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                # Type A satellite
                satellites.append(Satellite(orbit_radius=100, speed=0.03, color=SATELLITE_RED))
            elif event.key == pygame.K_2:
                # Type B satellite
                satellites.append(Satellite(orbit_radius=180, speed=0.015, color=SATELLITE_GREEN))

    for sat in satellites:
        sat.update()
        sat.draw(screen)

    draw_ui()
    pygame.display.flip()

pygame.quit()
