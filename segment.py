import pygame
import pymunk
import math
import random
from constants import *
from geometry_utils import simplify_polygon

class Segment:
    def __init__(self, pos, color, pixels, bounding_rect):
        self.color = color
        self.pixels = pixels
        self.bounding_rect = bounding_rect
        
        mass = 1
        moment = pymunk.moment_for_box(mass, (bounding_rect.width, bounding_rect.height))
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos  # pos is now a tuple, so this should work correctly

        points = self.get_polygon_points()
        if len(points) >= 3:
            self.shape = pymunk.Poly(self.body, points)
        else:
            self.shape = pymunk.Poly.create_box(self.body, (bounding_rect.width, bounding_rect.height))
        
        self.shape.friction = 0.5
        self.shape.elasticity = 0.3

        # Apply a random initial velocity
        impulse = pygame.math.Vector2(random.uniform(-100, 100), random.uniform(-100, 0))
        self.body.apply_impulse_at_local_point((impulse.x, impulse.y))  # Convert Vector2 to tuple

        # Apply a random angular velocity
        self.body.angular_velocity = random.uniform(-10, 10)

    def get_polygon_points(self):
        points = []
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel:
                    points.append((x - self.bounding_rect.width // 2, y - self.bounding_rect.height // 2))
        return simplify_polygon(points)

    def draw(self, surface):
        rotated_surface = pygame.Surface(self.bounding_rect.size, pygame.SRCALPHA)
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel:
                    rotated_surface.set_at((x, y), self.color)
        rotated_surface = pygame.transform.rotate(rotated_surface, -math.degrees(self.body.angle))
        pos = self.body.position
        surface.blit(rotated_surface, rotated_surface.get_rect(center=(int(pos.x), int(pos.y))))

    def should_remove(self):
        pos = self.body.position
        return pos.y > HEIGHT + 100 or pos.x < -100 or pos.x > WIDTH + 100