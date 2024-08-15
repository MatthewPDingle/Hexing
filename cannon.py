import pygame
from pygame.math import Vector2
from constants import *

class Cannon:
    def __init__(self, x, y):
        self.base_pos = Vector2(x, y)
        self.angle = 0

    def move(self, direction):
        self.base_pos.x += direction * CANNON_MOVE_SPEED
        self.base_pos.x = max(CANNON_LENGTH, min(WIDTH - CANNON_LENGTH, self.base_pos.x))

    def rotate(self, direction):
        self.angle += direction * CANNON_ROTATION_SPEED
        self.angle = max(-180, min(0, self.angle))

    def get_end_pos(self):
        return self.base_pos + Vector2(CANNON_LENGTH, 0).rotate(self.angle)

    def draw(self, surface):
        cannon_rect = pygame.Rect(0, -CANNON_WIDTH // 2, CANNON_LENGTH, CANNON_WIDTH)
        cannon_surf = pygame.Surface((CANNON_LENGTH, CANNON_WIDTH), pygame.SRCALPHA)
        pygame.draw.rect(cannon_surf, CANNON_COLOR, cannon_rect)
        rotated_surf = pygame.transform.rotate(cannon_surf, -self.angle)
        rotated_rect = rotated_surf.get_rect(center=self.base_pos)
        surface.blit(rotated_surf, rotated_rect)