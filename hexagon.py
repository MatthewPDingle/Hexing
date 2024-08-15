import pygame
import pymunk
import math
import random
import os
from pygame.math import Vector2
from constants import *
from segment import Segment
from geometry_utils import simplify_polygon

class Hexagon:
    def __init__(self, space):
        self.space = space
        self.load_random_hexagon()
        self.create_body()
        self.shattered = False
        self.segments = []
        self.respawn_time = 0

    def load_random_hexagon(self):
        assets_folder = "assets"
        try:
            hexagon_files = [f for f in os.listdir(assets_folder) if f.endswith('.png')]
            if not hexagon_files:
                raise FileNotFoundError("No PNG files found in the assets folder.")
            
            random_file = random.choice(hexagon_files)
            original_hexagon = pygame.image.load(os.path.join(assets_folder, random_file))
            
            # Scale the hexagon to a reasonable size
            scale_factor = 0.5  # Adjust this value as needed
            new_size = (int(original_hexagon.get_width() * scale_factor), 
                        int(original_hexagon.get_height() * scale_factor))
            self.surface = pygame.transform.scale(original_hexagon, new_size)
            
            # Create a mask from the surface to get the actual shape
            self.mask = pygame.mask.from_surface(self.surface)
            
            # Find the bounding box of the non-transparent pixels
            self.bbox = self.mask.get_bounding_rects()[0]
            
            # Center the hexagon on the screen
            screen_center = (WIDTH // 2, HEIGHT // 2 - FLOOR_HEIGHT)
            self.position = (screen_center[0] - self.bbox.width // 2, 
                             screen_center[1] - self.bbox.height // 2)
            
            self.rect = self.surface.get_rect(topleft=self.position)
        except Exception as e:
            print(f"Error loading hexagon image: {e}")
            # Fallback to a colored surface if image loading fails
            self.surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.polygon(self.surface, (255, 0, 0), self.get_hexagon_points(50))
            self.mask = pygame.mask.from_surface(self.surface)
            self.bbox = self.mask.get_bounding_rects()[0]
            self.position = (WIDTH // 2 - 50, HEIGHT // 2 - FLOOR_HEIGHT - 50)
            self.rect = self.surface.get_rect(topleft=self.position)

    def get_hexagon_points(self, radius):
        points = []
        for i in range(6):
            angle = i * math.pi / 3 - math.pi / 2
            points.append((radius + radius * math.cos(angle), radius + radius * math.sin(angle)))
        return points

    def create_body(self):
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = (self.position[0] + self.bbox.width // 2, 
                              self.position[1] + self.bbox.height // 2)
        
        outline = self.mask.outline()
        local_outline = [(p[0] - self.bbox.width // 2, p[1] - self.bbox.height // 2) for p in outline]
        simplified_outline = simplify_polygon(local_outline)  # Using the imported function
        
        self.shape = pymunk.Poly(self.body, simplified_outline)
        self.shape.collision_type = 2
        self.space.add(self.body, self.shape)

    def shatter(self):
        if not self.shattered:
            self.shattered = True
            self.segments = self.segment_hexagon()
            for segment in self.segments:
                self.space.add(segment.body, segment.shape)
            self.space.remove(self.body, self.shape)
            self.respawn_time = pygame.time.get_ticks() + HEXAGON_RESPAWN_TIME
            return self.segments
        return []

    def flood_fill(self, surface, start_pos, target_color, replacement_color):
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

    def segment_hexagon(self):
        segments = []
        width, height = self.surface.get_size()
        visited = set()

        for x in range(width):
            for y in range(height):
                if (x, y) not in visited and self.surface.get_at((x, y)).a > 0:
                    color = self.surface.get_at((x, y))
                    filled_pixels = self.flood_fill(self.surface, (x, y), color, (0, 0, 0, 0))
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

                        center = Vector2(bounding_rect.center) + Vector2(self.rect.topleft)
                        center_tuple = (center.x, center.y)
                        segments.append(Segment(center_tuple, color, segment_surface, bounding_rect))

        return segments

    def respawn(self):
        self.shattered = False
        self.load_random_hexagon()
        self.create_body()
        for segment in self.segments:
            self.space.remove(segment.body, segment.shape)
        self.segments = []

    def should_respawn(self):
        return self.shattered and pygame.time.get_ticks() >= self.respawn_time

    def draw(self, surface):
        if not self.shattered:
            surface.blit(self.surface, self.position)
        else:
            for segment in self.segments:
                segment.draw(surface)