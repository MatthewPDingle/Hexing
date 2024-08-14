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

# Cannon settings
CANNON_LENGTH = 50
CANNON_WIDTH = 10
CANNON_COLOR = (200, 200, 200)
CANNONBALL_RADIUS = 5
CANNONBALL_COLOR = (255, 255, 255)
CANNON_ROTATION_SPEED = 2
CANNON_MOVE_SPEED = 5
CANNON_FORCE = 1000

HEXAGON_RESPAWN_TIME = 1000

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

def create_hexagon(space):
    random_hexagon, hexagon_rect = load_random_hexagon()
    hexagon_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    hexagon_body.position = hexagon_rect.center
    
    # Create a more accurate hexagon shape
    radius = min(hexagon_rect.width, hexagon_rect.height) / 2
    points = []
    for i in range(6):
        angle = i * math.pi / 3 - math.pi / 2
        point = (radius * math.cos(angle), radius * math.sin(angle))
        points.append(point)
    
    hexagon_shape = pymunk.Poly(hexagon_body, points)
    hexagon_shape.collision_type = 2
    space.add(hexagon_body, hexagon_shape)
    return random_hexagon, hexagon_rect, hexagon_body, hexagon_shape

class Cannon:
    def __init__(self):
        self.base_pos = Vector2(WIDTH // 2, HEIGHT - FLOOR_HEIGHT)
        self.angle = 0  # Angle in degrees, 0 is pointing right, negative is upwards

    def move(self, direction):
        self.base_pos.x += direction * CANNON_MOVE_SPEED
        self.base_pos.x = max(CANNON_LENGTH, min(WIDTH - CANNON_LENGTH, self.base_pos.x))

    def rotate(self, direction):
        self.angle += direction * CANNON_ROTATION_SPEED
        self.angle = max(-180, min(0, self.angle))  # Limit angle between -180 and 0 degrees

    def get_end_pos(self):
        return self.base_pos + Vector2(CANNON_LENGTH, 0).rotate(self.angle)

    def draw(self, surface):
        cannon_rect = pygame.Rect(0, -CANNON_WIDTH // 2, CANNON_LENGTH, CANNON_WIDTH)
        cannon_surf = pygame.Surface((CANNON_LENGTH, CANNON_WIDTH), pygame.SRCALPHA)
        pygame.draw.rect(cannon_surf, CANNON_COLOR, cannon_rect)
        rotated_surf = pygame.transform.rotate(cannon_surf, -self.angle)
        rotated_rect = rotated_surf.get_rect(center=self.base_pos)
        surface.blit(rotated_surf, rotated_rect)

class Cannonball:
    def __init__(self, pos, angle):
        self.body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, CANNONBALL_RADIUS))
        self.body.position = pos.x, pos.y
        self.shape = pymunk.Circle(self.body, CANNONBALL_RADIUS)
        self.shape.elasticity = 0.8
        self.shape.friction = 0.5
        self.shape.collision_type = 1  # Assign a collision type for later use
        
        force = Vector2(CANNON_FORCE, 0).rotate(angle)
        self.body.apply_impulse_at_local_point((force.x, force.y))

    def draw(self, surface):
        pos = self.body.position
        pygame.draw.circle(surface, CANNONBALL_COLOR, (int(pos.x), int(pos.y)), CANNONBALL_RADIUS)

    def should_remove(self):
        pos = self.body.position
        velocity = self.body.velocity
        return (pos.x < 0 or pos.x > WIDTH or pos.y > HEIGHT or 
                (abs(velocity.x) < 1 and abs(velocity.y) < 1 and pos.y > HEIGHT - FLOOR_HEIGHT - CANNONBALL_RADIUS))


# Collision handler
def cannonball_hexagon_collision(arbiter, space, data):
    if not data['shattered']:
        hexagon_shape = arbiter.shapes[1]
        hexagon_body = hexagon_shape.body
        pos = hexagon_body.position
        data['shattered'] = True
        data['segments'] = segment_hexagon(data['hexagon_surface'])
        for segment in data['segments']:
            space.add(segment.body, segment.shape)
        space.remove(hexagon_body, hexagon_shape)
        data['respawn_time'] = pygame.time.get_ticks() + HEXAGON_RESPAWN_TIME
    return True

# Segment class for shattered pieces
class Segment:
    def __init__(self, pos, color, pixels, bounding_rect):
        self.color = color
        self.pixels = pixels
        self.bounding_rect = bounding_rect

        mass = 1
        moment = pymunk.moment_for_box(mass, (bounding_rect.width, bounding_rect.height))
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos.x, pos.y

        points = self.get_polygon_points()
        if len(points) >= 3:
            self.shape = pymunk.Poly(self.body, points)
        else:
            self.shape = pymunk.Poly.create_box(self.body, (bounding_rect.width, bounding_rect.height))
        
        self.shape.friction = 0.5
        self.shape.elasticity = 0.3

    def get_polygon_points(self):
        points = []
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel:
                    points.append((x - self.bounding_rect.width // 2, y - self.bounding_rect.height // 2))
        return self.simplify_polygon(points)

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
        rotated_surface = pygame.transform.rotate(rotated_surface, -math.degrees(self.body.angle))
        pos = self.body.position
        surface.blit(rotated_surface, rotated_surface.get_rect(center=(int(pos.x), int(pos.y))))

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
random_hexagon, hexagon_rect, hexagon_body, hexagon_shape = create_hexagon(space)
all_segments = []  # Keep track of all segments, including those from previous hexagons
shattered = False
clock = pygame.time.Clock()
cannon = Cannon()
cannonballs = []

# Set up collision handler
handler = space.add_collision_handler(1, 2)  # 1 for cannonball, 2 for hexagon
handler.data['shattered'] = False
handler.data['hexagon_surface'] = random_hexagon
handler.data['segments'] = []
handler.data['respawn_time'] = 0
handler.begin = cannonball_hexagon_collision

running = True
while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                cannon_end = cannon.get_end_pos()
                new_cannonball = Cannonball(cannon_end, cannon.angle)
                space.add(new_cannonball.body, new_cannonball.shape)
                cannonballs.append(new_cannonball)
            elif event.key == pygame.K_ESCAPE:
                running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        cannon.move(-1)
    if keys[pygame.K_RIGHT]:
        cannon.move(1)
    if keys[pygame.K_UP]:
        cannon.rotate(-1)  # Negative to rotate upwards
    if keys[pygame.K_DOWN]:
        cannon.rotate(1)  # Positive to rotate downwards

    screen.fill(BLACK)
    pygame.draw.rect(screen, FLOOR_COLOR, (0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT))

    if not handler.data['shattered']:
        screen.blit(random_hexagon, hexagon_rect)
    else:
        if current_time >= handler.data['respawn_time']:
            # Respawn the hexagon without removing old segments
            random_hexagon, hexagon_rect, hexagon_body, hexagon_shape = create_hexagon(space)
            handler.data['shattered'] = False
            handler.data['hexagon_surface'] = random_hexagon
            all_segments.extend(handler.data['segments'])
            handler.data['segments'] = []

    # Draw all segments, including those from previous hexagons
    for segment in all_segments + handler.data['segments']:
        segment.draw(screen)

    cannonballs = [cb for cb in cannonballs if not cb.should_remove()]
    for cannonball in cannonballs:
        cannonball.draw(screen)
        if cannonball.should_remove():
            space.remove(cannonball.body, cannonball.shape)

    cannon.draw(screen)

    space.step(1/60.0)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()