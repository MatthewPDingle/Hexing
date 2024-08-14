import pygame
import pymunk
import pymunk.pygame_util
import sys
import math
import os
import random
from pygame.math import Vector2

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hexagon Shatter POC with Pymunk")

# Colors
BLACK = (0, 0, 0)
FLOOR_COLOR = (50, 50, 50)

# Floor settings
FLOOR_HEIGHT = 100

# Pymunk space
space = pymunk.Space()
space.gravity = (0, 900)  # Adjust gravity as needed

# Pymunk static line for the floor
floor_shape = pymunk.Segment(space.static_body, (0, HEIGHT - FLOOR_HEIGHT), (WIDTH, HEIGHT - FLOOR_HEIGHT), 5)
floor_shape.friction = 0.4
space.add(floor_shape)

# Load hexagon images
assets_folder = "assets"
try:
    hexagon_files = [f for f in os.listdir(assets_folder) if f.endswith('.png')]
    if not hexagon_files:
        raise FileNotFoundError("No PNG files found in the assets folder.")
except Exception as e:
    print(f"Error loading images: {e}")
    pygame.quit()
    sys.exit()

def load_random_hexagon():
    original_hexagon = pygame.image.load(os.path.join(assets_folder, random.choice(hexagon_files)))
    hexagon_size = (original_hexagon.get_width() // 2, original_hexagon.get_height() // 2)
    random_hexagon = pygame.transform.scale(original_hexagon, hexagon_size)
    hexagon_rect = random_hexagon.get_rect(center=(WIDTH // 2, HEIGHT // 2 - FLOOR_HEIGHT))
    return random_hexagon, hexagon_rect

# Segment class for shattered pieces
class Segment:
    def __init__(self, pos, color, pixels, bounding_rect):
        self.color = color
        self.pixels = pixels
        self.bounding_rect = bounding_rect

        # Create pymunk body and shape
        mass = 1
        moment = pymunk.moment_for_box(mass, (bounding_rect.width, bounding_rect.height))
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos.x, pos.y  # Convert Vector2 to tuple

        # Create a polygon shape from the pixel data
        points = self.get_polygon_points()
        if len(points) >= 3:  # Ensure we have at least a triangle
            self.shape = pymunk.Poly(self.body, points)
        else:
            # Fallback to a simple box if we don't have enough points
            self.shape = pymunk.Poly.create_box(self.body, (bounding_rect.width, bounding_rect.height))
        
        self.shape.friction = 0.5
        self.shape.elasticity = 0.3

        space.add(self.body, self.shape)

    def get_polygon_points(self):
        points = []
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel:
                    points.append((x - self.bounding_rect.width // 2, y - self.bounding_rect.height // 2))
        
        # Simplify the polygon to reduce the number of points
        simplified_points = self.simplify_polygon(points)
        return simplified_points

    def simplify_polygon(self, points, tolerance=1.0):
        if len(points) <= 3:
            return points
        
        def point_line_distance(point, start, end):
            if start == end:
                return math.hypot(point[0] - start[0], point[1] - start[1])
            n = abs((end[0] - start[0]) * (start[1] - point[1]) - (start[0] - point[0]) * (end[1] - start[1]))
            d = math.hypot(end[0] - start[0], end[1] - start[1])
            return n / d

        def rdp(points, epsilon, dist):
            dmax = 0.0
            index = 0
            for i in range(1, len(points) - 1):
                d = dist(points[i], points[0], points[-1])
                if d > dmax:
                    index = i
                    dmax = d
            if dmax >= epsilon:
                results = rdp(points[:index+1], epsilon, dist)[:-1] + rdp(points[index:], epsilon, dist)
            else:
                results = [points[0], points[-1]]
            return results

        return rdp(points, tolerance, point_line_distance)

    def draw(self, surface):
        rotated_surface = pygame.Surface(self.bounding_rect.size, pygame.SRCALPHA)
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel:
                    rotated_surface.set_at((x, y), self.color)
        rotated_surface = pygame.transform.rotate(rotated_surface, -self.body.angle * 180 / 3.14)
        pos = Vector2(self.body.position)
        surface.blit(rotated_surface, rotated_surface.get_rect(center=pos))

# Flood fill function
def flood_fill(surface, start_pos, target_color, replacement_color):
    width, height = surface.get_size()
    stack = [start_pos]
    filled_pixels = []

    while stack:
        x, y = stack.pop()
        if surface.get_at((x, y)) != target_color:
            continue

        surface.set_at((x, y), replacement_color)
        filled_pixels.append((x, y))

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                stack.append((nx, ny))

    return filled_pixels

# Function to segment the hexagon
def segment_hexagon(surface):
    segments = []
    width, height = surface.get_size()
    visited = set()

    for x in range(width):
        for y in range(height):
            if (x, y) not in visited and surface.get_at((x, y)).a > 0:
                color = surface.get_at((x, y))
                filled_pixels = flood_fill(surface, (x, y), color, (0, 0, 0, 0))
                visited.update(filled_pixels)

                if len(filled_pixels) > 10:  # Ignore very small segments
                    min_x = min(p[0] for p in filled_pixels)
                    min_y = min(p[1] for p in filled_pixels)
                    max_x = max(p[0] for p in filled_pixels)
                    max_y = max(p[1] for p in filled_pixels)

                    bounding_rect = pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
                    segment_surface = [[False for _ in range(bounding_rect.width)] 
                                       for _ in range(bounding_rect.height)]
                    
                    for px, py in filled_pixels:
                        segment_surface[py - min_y][px - min_x] = True

                    center = Vector2(bounding_rect.center) + Vector2(hexagon_rect.topleft)
                    segments.append(Segment(center, color, segment_surface, bounding_rect))

    return segments

# Main game loop
random_hexagon, hexagon_rect = load_random_hexagon()
segments = []
shattered = False
clock = pygame.time.Clock()

draw_options = pymunk.pygame_util.DrawOptions(screen)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if shattered:
                    # Remove old segments from space
                    for segment in segments:
                        space.remove(segment.body, segment.shape)
                    # Load a new hexagon
                    random_hexagon, hexagon_rect = load_random_hexagon()
                    shattered = False
                    segments = []
                else:
                    # Shatter the current hexagon
                    segments = segment_hexagon(random_hexagon.copy())
                    shattered = True
            elif event.key == pygame.K_ESCAPE:
                running = False

    screen.fill(BLACK)
    pygame.draw.rect(screen, FLOOR_COLOR, (0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT))

    if not shattered:
        screen.blit(random_hexagon, hexagon_rect)
    else:
        space.step(1/60.0)
        for segment in segments:
            segment.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()