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

# --- AI Action & Goal Definitions ---
class Action:
    """A simple class to represent an action the AI can take."""
    def __init__(self, action_type, **kwargs):
        self.action_type = action_type
        self.params = kwargs
    
    def __repr__(self):
        return f"Action({self.action_type}, {self.params})"

def goal_stack_two_boxes(graph):
    """A goal function that checks if two boxes are stacked."""
    boxes = [ (node, data) for node, data in graph.nodes(data=True) if data['obj_type'] == 'box' ]
    if len(boxes) < 2: return False

    for i in range(len(boxes)):
        for j in range(len(boxes)):
            if i == j: continue
            
            box1_node, box1_data = boxes[i]
            box2_node, box2_data = boxes[j]

            pos1 = box1_data['physics']['position']
            pos2 = box2_data['physics']['position']
            
            # Check if box1 is roughly on top of box2 and they are both stable
            is_horizontally_aligned = abs(pos1[0] - pos2[0]) < 25
            is_vertically_stacked = pos1[1] < pos2[1] and abs(pos1[1] - (pos2[1] - 50)) < 10
            is_stable = box1_data['physics']['is_sleeping'] and box2_data['physics']['is_sleeping']

            if is_horizontally_aligned and is_vertically_stacked and is_stable:
                print(f"GOAL MET: {box1_node} is stacked on {box2_node}")
                return True
    return False

# --- CSM Components ---
class CSM_Oracle:
    """The reasoning engine. It can predict the future by running headless simulations."""
    def _reconstruct_space_from_graph(self, graph, action=None):
        headless_space = pymunk.Space()
        headless_space.gravity = (0, 981)
        
        headless_space.sleep_time_threshold = 0.5
        headless_space.idle_speed_threshold = 1.0
        
        headless_world_objects = {}

        if action and action.action_type == 'spawn_object':
            pass

        for node_id, data in graph.nodes(data=True):
            obj_type = data['obj_type']; props = data['properties']; physics = data['physics']
            if obj_type == 'ground':
                body = headless_space.static_body
                shape = pymunk.Segment(body, (0, SCREEN_HEIGHT - 50), (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 5)
                # --- FIX: The ground shape was created but never added to the headless space. ---
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
                body.position = physics['position']; body.velocity = physics['velocity']; body.angle = physics['angle']
                headless_space.add(body, shape)
            
            shape.friction = props.get('friction', 0.7); shape.elasticity = props.get('elasticity', 0.5)
            body.alexandria_id = node_id
            headless_world_objects[body.id] = {"uuid": node_id, "obj_type": obj_type, "properties": copy.deepcopy(props)}
        
        return headless_space, headless_world_objects

    def predict_future(self, start_state_graph, duration_seconds=5, action=None):
        headless_space, headless_world_objects = self._reconstruct_space_from_graph(start_state_graph, action)
        steps = int(duration_seconds * 60)
        for _ in range(steps): headless_space.step(1.0 / 60.0)
        return get_graph_from_space(headless_space, headless_world_objects)

class CSM_Planner:
    """The problem-solving component. Uses the Oracle to find a sequence of actions to achieve a goal."""
    def __init__(self, oracle):
        self.oracle = oracle
        self.max_attempts = 100 # To prevent infinite loops

    def find_plan(self, initial_state, goal_func):
        print("\n--- PLANNER: Attempting to find a plan with an intelligent strategy... ---")
        
        boxes = [ (node, data) for node, data in initial_state.nodes(data=True) if data['obj_type'] == 'box' ]
        if not boxes:
            print("--- PLANNER: Failed. Need at least one box in the scene to act as a base. ---")
            return None

        base_candidates = [
            (node, data) for node, data in boxes 
            if data['physics']['is_sleeping']
        ]

        if not base_candidates:
            print("--- PLANNER: Failed. Could not find a stable base box. Let objects settle first. ---")
            return None

        for i in range(self.max_attempts):
            print(f"--- PLANNER: Attempt {i+1}/{self.max_attempts} ---")
            
            base_node_id, base_data = random.choice(base_candidates)
            base_pos = base_data['physics']['position']
            
            jitter_x = random.uniform(-15, 15)
            spawn_pos = (base_pos[0] + jitter_x, base_pos[1] - 55)
            
            sim_graph = copy.deepcopy(initial_state)
            
            new_box_id = f"sim_box_{i}"
            sim_graph.add_node(new_box_id, 
                obj_type='box',
                properties={'mass': 15, 'dimensions': {'size': (50,50)}, 'friction': 0.6, 'elasticity': 0.5},
                physics={'position': spawn_pos, 'velocity': (0,0), 'angle': 0, 'is_sleeping': False}
            )
            
            action_plan = [Action('spawn_box', position=spawn_pos)]

            final_state = self.oracle.predict_future(sim_graph, duration_seconds=10)

            if goal_func(final_state):
                print(f"--- PLANNER: SUCCESS! Plan found after {i+1} attempts. ---")
                print(f"PLAN: {action_plan}")
                return action_plan
        
        print(f"--- PLANNER: FAILED. No solution found after {self.max_attempts} attempts. ---")
        return None

# --- The Main Simulation Class ---
class Crucible:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Alexandria - 'S' State, 'P' Predict, 'G' Goal")
        self.clock = pygame.time.Clock()
        self.running = True
        self.space = pymunk.Space()
        self.space.gravity = (0, 981)
        
        self.space.sleep_time_threshold = 0.5
        self.space.idle_speed_threshold = 1.0
        
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.world_objects = {}
        self.oracle = CSM_Oracle()
        self.planner = CSM_Planner(self.oracle)
        self.add_static_ground()

    def add_static_ground(self):
        ground_body = self.space.static_body
        ground_shape = pymunk.Segment(ground_body, (0, SCREEN_HEIGHT - 50), (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 5)
        ground_shape.friction = 0.8; ground_shape.elasticity = 0.4
        ground_shape.color = pygame.Color("darkgrey")
        self.space.add(ground_shape)
        ground_id = "static_ground_0"
        self.world_objects[ground_body.id] = {"uuid": ground_id, "obj_type": "ground", "properties": {"friction": 0.8, "elasticity": 0.4}}
        ground_body.alexandria_id = ground_id

    def spawn_object(self, pos):
        obj_uuid = f"obj_{uuid.uuid4().hex[:6]}"
        color = pygame.Color(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        properties = {}
        if random.random() > 0.5:
            obj_type = "ball"; mass = 10; radius = 25
            properties['dimensions'] = {'radius': radius}
            moment = pymunk.moment_for_circle(mass, 0, radius); body = pymunk.Body(mass, moment)
            shape = pymunk.Circle(body, radius); shape.elasticity = 0.6
        else:
            obj_type = "box"; mass = 15; size = (50, 50)
            properties['dimensions'] = {'size': size}
            moment = pymunk.moment_for_box(mass, size); body = pymunk.Body(mass, moment)
            shape = pymunk.Poly.create_box(body, size); shape.elasticity = 0.5
        body.position = pos; shape.friction = 0.7; shape.color = color
        self.space.add(body, shape)
        properties.update({"mass": mass, "friction": shape.friction, "elasticity": shape.elasticity, "color": color.normalize()})
        self.world_objects[body.id] = {"uuid": obj_uuid, "obj_type": obj_type, "properties": properties}
        body.alexandria_id = obj_uuid
        print(f"Spawned '{obj_type}' with ID {obj_uuid}.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: self.spawn_object(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    print("\n--- CURRENT WORLD STATE ---")
                    state_graph = get_graph_from_space(self.space, self.world_objects)
                    for node, data in state_graph.nodes(data=True): print(f"Node: {node}"); pprint.pprint(data, indent=2)
                elif event.key == pygame.K_p:
                    current_state = get_graph_from_space(self.space, self.world_objects)
                    predicted_state = self.oracle.predict_future(current_state, duration_seconds=3)
                    print("\n--- ORACLE PREDICTION (T+3s) ---")
                    for node, data in predicted_state.nodes(data=True): print(f"Node: {node}"); pprint.pprint(data, indent=2)
                elif event.key == pygame.K_g:
                    current_state = get_graph_from_space(self.space, self.world_objects)
                    self.planner.find_plan(current_state, goal_stack_two_boxes)

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

