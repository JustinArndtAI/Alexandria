import pygame
import pymunk
import pymunk.pygame_util
import random

# --- Constants ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

class Crucible:
    """
    The main class for our 2D physics sandbox.
    This class initializes the environment, runs the simulation loop,
    and handles user interactions.
    """
    def __init__(self):
        """Initializes the Crucible environment."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("The Alexandria Project - The Crucible")
        self.clock = pygame.time.Clock()
        self.running = True

        # Pymunk physics setup
        self.space = pymunk.Space()
        self.space.gravity = (0, 981) # Y-axis is inverted in Pygame (0 is top)
        
        # Drawing options for Pymunk
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)

        # Add the static ground
        self.add_static_ground()
        
        # A list to hold all dynamic bodies we create
        self.dynamic_bodies = []

    def add_static_ground(self):
        """Creates a static line segment at the bottom of the screen."""
        ground_body = self.space.static_body
        ground_shape = pymunk.Segment(ground_body, (0, SCREEN_HEIGHT - 50), (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 5)
        ground_shape.friction = 0.8
        ground_shape.elasticity = 0.4
        self.space.add(ground_shape)
        print("Crucible Initialized: Static ground created.")

    def spawn_object(self, pos):
        """Spawns a dynamic object (a ball or a box) at the given position."""
        if random.random() > 0.5:
            # Spawn a ball
            mass = 10
            radius = 25
            moment = pymunk.moment_for_circle(mass, 0, radius)
            body = pymunk.Body(mass, moment)
            body.position = pos
            shape = pymunk.Circle(body, radius)
            shape.friction = 0.7
            shape.elasticity = 0.6
        else:
            # Spawn a box
            mass = 15
            size = (50, 50)
            moment = pymunk.moment_for_box(mass, size)
            body = pymunk.Body(mass, moment)
            body.position = pos
            shape = pymunk.Poly.create_box(body, size)
            shape.friction = 0.6
            shape.elasticity = 0.5
            
        self.space.add(body, shape)
        self.dynamic_bodies.append(body)
        print(f"Object spawned at {pos}. Total dynamic bodies: {len(self.dynamic_bodies)}")

    def handle_events(self):
        """Handles user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    self.spawn_object(event.pos)

    def update(self):
        """Updates the physics simulation."""
        # Step the physics simulation forward
        # The dt (delta time) should be constant for a stable simulation
        dt = 1.0 / 60.0
        self.space.step(dt)

    def draw(self):
        """Draws everything to the screen."""
        self.screen.fill((217, 217, 217)) # A light grey background
        
        # Use Pymunk's debug draw feature to draw all shapes
        self.space.debug_draw(self.draw_options)
        
        pygame.display.flip()

    def run(self):
        """The main loop of the simulation."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60) # Limit the framerate to 60 FPS

        pygame.quit()
        print("Crucible simulation terminated.")

if __name__ == "__main__":
    crucible_sim = Crucible()
    crucible_sim.run()