import pygame
import pymunk
from constants import *
from cannon import Cannon
from hexagon import Hexagon
from cannonball import Cannonball
from segment import Segment

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)
        
        self.create_floor()
        self.cannon = Cannon(WIDTH // 2, HEIGHT - FLOOR_HEIGHT)
        self.hexagon = Hexagon(self.space)
        self.cannonballs = []
        self.all_segments = []

        self.setup_collision_handler()  # Initialize all_segments here

    def create_floor(self):
        floor_shape = pymunk.Segment(self.space.static_body, (0, HEIGHT - FLOOR_HEIGHT), (WIDTH, HEIGHT - FLOOR_HEIGHT), 5)
        floor_shape.friction = 0.4
        self.space.add(floor_shape)

    def setup_collision_handler(self):
        handler = self.space.add_collision_handler(1, 2)  # 1 for cannonball, 2 for hexagon
        handler.begin = self.on_collision

    def on_collision(self, arbiter, space, data):
        if not self.hexagon.shattered:
            new_segments = self.hexagon.shatter()
            self.all_segments.extend(new_segments)
        return True

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.cannon.move(-1)
        if keys[pygame.K_RIGHT]:
            self.cannon.move(1)
        if keys[pygame.K_UP]:
            self.cannon.rotate(-1)
        if keys[pygame.K_DOWN]:
            self.cannon.rotate(1)

        #self.hexagon.update()
        self.update_cannonballs()
        self.update_segments()
        
        if self.hexagon.should_respawn():
            self.hexagon = Hexagon(self.space)

        self.space.step(1/60.0)

    def update_segments(self):
        for segment in self.all_segments[:]:
            if segment.should_remove():
                self.space.remove(segment.body, segment.shape)
                self.all_segments.remove(segment)

    def update_cannonballs(self):
        for cannonball in self.cannonballs[:]:
            if cannonball.should_remove():
                self.space.remove(cannonball.body, cannonball.shape)
                self.cannonballs.remove(cannonball)

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, FLOOR_COLOR, (0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT))
        
        self.hexagon.draw(self.screen)
        for segment in self.all_segments:
            segment.draw(self.screen)
        
        self.cannon.draw(self.screen)
        
        for cannonball in self.cannonballs:
            cannonball.draw(self.screen)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.fire_cannonball()

    def fire_cannonball(self):
        end_pos = self.cannon.get_end_pos()
        cannonball = Cannonball(end_pos, self.cannon.angle)
        self.space.add(cannonball.body, cannonball.shape)
        self.cannonballs.append(cannonball)