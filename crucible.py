import pygame
import pymunk
import pymunk.pygame_util
import random
import uuid
import networkx as nx
import pprint
import copy

# --- Constants ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

# --- Helper Function: State Extraction ---
def get_graph_from_space(space, world_objects):
    """
    Extracts the complete state of a Pymunk space into a NetworkX graph.
    This is the "perception" of our AI.
    """
    graph = nx.DiGraph()
    all_bodies = list(space.bodies) + [space.static_body]

    for body in all_bodies:
        if not hasattr(body, 'alexandria_id'): continue

        obj_id = body.alexandria_id
        static_props = world_objects[body.id]

        node_attributes = {
            "obj_type": static_props["obj_type"],
            "properties": static_props["properties"],
            "physics": {
                "position": (round(body.position.x, 2), round(body.position.y, 2)),
                "velocity": (round(body.velocity.x, 2), round(body.velocity.y, 2)),
                "angle": round(body.angle, 2),
                "is_sleeping": body.is_sleeping
            }
        }
        graph.add_node(obj_id, **node_attributes)
    
    return graph

# --- The Oracle Class ---
class CSM_Oracle:
    """
    The reasoning engine. It can predict the future by running headless simulations.
    This is the core of our Causal State Machine.
    """
    def _reconstruct_space_from_graph(self, graph):
        """Rebuilds a Pymunk space from a given world state graph."""
        headless_space = pymunk.Space()
        headless_space.gravity = (0, 981)
        
        # This will hold the ontology for the new headless space
        headless_world_objects = {}

        for node_id, data in graph.nodes(data=True):
            obj_type = data['obj_type']
            props = data['properties']
            physics = data['physics']

            if obj_type == 'ground':
                body = headless_space.static_body
                shape = pymunk.Segment(body, (0, SCREEN_HEIGHT - 50), (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 5)
                shape.friction = props['friction']
                shape.elasticity = props['elasticity']
                headless_space.add(shape)
            else:
                mass = props['mass']
                if obj_type == 'ball':
                    radius = props['dimensions']['radius']
                    moment = pymunk.moment_for_circle(mass, 0, radius)
                    body = pymunk.Body(mass, moment)
                    shape = pymunk.Circle(body, radius)
                elif obj_type == 'box':
                    size = props['dimensions']['size']
                    moment = pymunk.moment_for_box(mass, size)
                    body = pymunk.Body(mass, moment)
                    shape = pymunk.Poly.create_box(body, size)
                
                body.position = physics['position']
                body.velocity = physics['velocity']
                body.angle = physics['angle']
                shape.friction = props['friction']
                shape.elasticity = props['elasticity']
                headless_space.add(body, shape)

            # Rebuild the metadata needed for the next state extraction
            body.alexandria_id = node_id
            headless_world_objects[body.id] = {
                "uuid": node_id,
                "obj_type": obj_type,
                "properties": copy.deepcopy(props) # Use deepcopy for safety
            }
        
        return headless_space, headless_world_objects

    def predict_future(self, start_state_graph, duration_seconds=5):
        """
        Takes a world state, simulates it forward, and returns the final state.
        """
        print(f"\n--- ORACLE: Simulating {duration_seconds} seconds into the future... ---")
        headless_space, headless_world_objects = self._reconstruct_space_from_graph(start_state_graph)

        # Run the simulation
        steps = int(duration_seconds * 60)
        for _ in range(steps):
            headless_space.step(1.0 / 60.0)

        # Extract and return the final state
        final_state_graph = get_graph_from_space(headless_space, headless_world_objects)
        print("--- ORACLE: Simulation complete. Returning final state. ---")
        return final_state_graph

# --- The Main Simulation Class ---
class Crucible:
    """
    The main class for our 2D physics sandbox.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Alexandria - Press 'S' to print state, 'P' to predict future")
        self.clock = pygame.time.Clock()
        self.running = True
        self.space = pymunk.Space()
        self.space.gravity = (0, 981)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.world_objects = {}
        self.oracle = CSM_Oracle()
        self.add_static_ground()

    def add_static_ground(self):
        ground_body = self.space.static_body
        ground_shape = pymunk.Segment(ground_body, (0, SCREEN_HEIGHT - 50), (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 5)
        ground_shape.friction = 0.8; ground_shape.elasticity = 0.4
        ground_shape.color = pygame.Color("darkgrey")
        self.space.add(ground_shape)
        ground_id = "static_ground_0"
        self.world_objects[ground_body.id] = {
            "uuid": ground_id, "obj_type": "ground",
            "properties": {"friction": ground_shape.friction, "elasticity": ground_shape.elasticity}
        }
        ground_body.alexandria_id = ground_id

    def spawn_object(self, pos):
        obj_uuid = f"obj_{uuid.uuid4().hex[:6]}"
        color = pygame.Color(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        
        properties = {}
        if random.random() > 0.5:
            obj_type = "ball"; mass = 10; radius = 25
            properties['dimensions'] = {'radius': radius}
            moment = pymunk.moment_for_circle(mass, 0, radius)
            body = pymunk.Body(mass, moment)
            shape = pymunk.Circle(body, radius)
            shape.elasticity = 0.6
        else:
            obj_type = "box"; mass = 15; size = (50, 50)
            properties['dimensions'] = {'size': size}
            moment = pymunk.moment_for_box(mass, size)
            body = pymunk.Body(mass, moment)
            shape = pymunk.Poly.create_box(body, size)
            shape.elasticity = 0.5
        
        body.position = pos
        shape.friction = 0.7; shape.color = color
        self.space.add(body, shape)
        
        properties.update({"mass": mass, "friction": shape.friction, "elasticity": shape.elasticity, "color": color.normalize()})
        self.world_objects[body.id] = {"uuid": obj_uuid, "obj_type": obj_type, "properties": properties}
        body.alexandria_id = obj_uuid
        print(f"Spawned '{obj_type}' with ID {obj_uuid} at {pos}.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: self.spawn_object(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    print("\n--- EXTRACTING CURRENT WORLD STATE ---")
                    state_graph = get_graph_from_space(self.space, self.world_objects)
                    for node, data in state_graph.nodes(data=True):
                        print(f"Node: {node}"); pprint.pprint(data, indent=2)
                    print("------------------------------------\n")
                elif event.key == pygame.K_p:
                    current_state = get_graph_from_space(self.space, self.world_objects)
                    predicted_state = self.oracle.predict_future(current_state, duration_seconds=3)
                    print("\n--- ORACLE PREDICTION (T+3s) ---")
                    for node, data in predicted_state.nodes(data=True):
                        print(f"Node: {node}"); pprint.pprint(data, indent=2)
                    print("--------------------------------\n")

    def run(self):
        while self.running:
            self.handle_events(); self.space.step(1/60.0)
            self.screen.fill((217, 217, 217))
            self.space.debug_draw(self.draw_options)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    crucible_sim = Crucible()
    crucible_sim.run()