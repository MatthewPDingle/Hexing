import pygame
import pymunk
from pygame.math import Vector2
from constants import *

class Cannonball:
    def __init__(self, pos, angle):
        self.body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, CANNONBALL_RADIUS))
        self.body.position = (pos.x, pos.y)  # Convert Vector2 to tuple
        self.shape = pymunk.Circle(self.body, CANNONBALL_RADIUS)
        self.shape.elasticity = 0.8
        self.shape.friction = 0.5
        self.shape.collision_type = 1
        
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