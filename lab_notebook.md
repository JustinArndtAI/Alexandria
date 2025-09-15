The Alexandria Project - Experimental Log
This document contains the official results of the Gauntlet tests, comparing the Alexandria Causal State Machine (CSM) against a frontier Large Language Model (LLM).

Test 1: Prediction
Objective: To test the model's ability to predict the outcome of a simple, deterministic chain reaction.

Setup:

Run crucible.py.

Press 'R' to spawn a ramp.

Press 'D' to spawn a domino at the bottom of the ramp.

Press 'C' to spawn a ball at the top of the ramp.

Immediately press 'S' to get the object IDs and current state.

Immediately press 'T', type predict future, and press Enter.

CSM Prompt:

predict future

CSM Response:
(CSM provides a precise final position based on its internal simulation.)

LLM System Prompt (Provide this to the LLM first):

You are an AI assistant analyzing a 2D physics simulation. The world contains balls (radius 25, mass 10), boxes (size 50x50, mass 15), and dominos (size 10x60, mass 5). A ramp is a static, angled line. All objects are affected by gravity. Your task is to reason about the physical outcomes based on the text descriptions I provide. Be precise and literal in your reasoning.

LLM User Prompt:

Here is the initial state of the simulation:
- A ramp exists with endpoints (440, 740) and (740, 640).
- A ball with ID obj_f12ca3 is at position (696.44, 622.98).
- A domino with ID obj_07e184 is at position (417.56, 715.03).

What will be the final resting position of the domino (obj_07e184) after 5 seconds?

LLM Response:

Short answer: **the domino will end up lying flat on its left side with its center at about (382.56, 740.03)** (x, y in the same coordinates you gave), oriented horizontally (long axis along −x).

Reasoning and arithmetic (literal, step-by-step):

Assumptions I use (stated explicitly so the numbers are reproducible):

* Coordinates are in the same 2D screen-like system you supplied and gravity acts in the +y direction (downwards).
* Object positions you gave are center positions, domino is initially upright (height = 60 along y, width = 10 along x).
* The ramp is a static line between p1 = (440,740) and p2 = (740,640). The ball (radius 25, mass 10) is above/right on that ramp and will roll *left* along the ramp under gravity toward the ramp’s left endpoint (440,740).
* The ball reaches the ramp’s left end and strikes the domino (the geometry makes collision effectively guaranteed); the hit knocks the domino over to the left and it comes to rest lying flat on the ground within the 5 s window. (I ignore small sliding/translation after the 90° fall — the dominant final configuration is domino flat to the left of its start.)

Geometry used to compute the final center:

1. Domino initial center: $C_0=(417.56,\;715.03)$. Domino half-width = 5, half-height = 30.
   Therefore the bottom-left corner (pivot for a leftward fall) is at

   $$
   P=(417.56-5,\;715.03+30)=(412.56,\;745.03).
   $$

2. Vector from that pivot to the domino center initially:

   $$
   r = C_0 - P = (5,\;-30).
   $$

3. If the domino rotates 90° clockwise (falls left) about that pivot, rotate $r$ by −90°:

   $$
   r' = \text{rotate}_{-90^\circ}(5,\,-30) = (-30,\,-5).
   $$

4. Final center after rotation:

   $$
   C_f = P + r' = (412.56-30,\;745.03-5) = (382.56,\;740.03).
   $$

So the final resting **center** is approximately **(382.56, 740.03)** and the domino lies horizontally with its long side spanning x ≈ \[352.56, 412.56] and y ≈ \[735.03, 745.03].

Caveats / uncertainty: small differences in friction, exact impact point, or additional translation from the collision could shift this by a few pixels; the calculation above gives the literal geometric outcome for a clean toppling about the bottom-left corner (the physically most likely clean outcome given the ball strikes the domino’s right/upper-right). If you want, I can give an alternate estimate if you expect the domino to pivot about a different corner or to be translated significantly by the impulse.


Analysis:
The CSM's prediction is correct by definition, as it is the direct output of the ground-truth physics simulation. The LLM correctly identifies the qualitative chain of events but fails on the quantitative prediction. It engages in "narrative physics," using a simplified geometric rotation model instead of simulating the actual dynamics of momentum, friction, and collision. The high precision of its answer (382.56, 740.03) is an illusion, as it is derived from a flawed causal model. This demonstrates the LLM's inability to perform true physical simulation, relying instead on plausible-sounding heuristics.

Test 2: Counterfactual Reasoning
Objective: To test the model's ability to modify a single parameter of its internal world model and predict a new outcome based on that change.

Setup:

Run crucible.py.

Press 'B' to spawn a single box in the middle of the screen.

Let the box fall and come to a complete rest on the ground.

Press 'S' to get the box's object ID (e.g., obj_123abc).

CSM Prompt:
(Press 'T' and type the following command, replacing <obj_id> with the actual ID of your box)

counterfactual mass <obj_id> 10

CSM Response:
Counterfactual Prediction: If obj_dd4ddb's mass was multiplied by 10.0, its final position would be (524.42, 720.1).

LLM User Prompt:
(After providing the system prompt, use the following template, replacing <obj_id> with the actual ID)

A box with ID <obj_id> and a mass of 15 rests on the ground. A second, identical box is dropped directly on top of it from a height of 200 pixels. The top box comes to rest on the bottom box.

Now for the counterfactual question: In the exact same scenario, what would happen differently if the bottom box (<obj_id>) had a mass of 150 (10 times its original mass)? Describe the final state of both boxes.

LLM Response:
Short answer first: in both the real scenario and the counterfactual the final *steady* state is the same — the two boxes end up stacked (top box sitting on the bottom box) and at rest on the ground. What changes is the *transient* motion during the impact and the sizes of transient contact forces.

Below I state the assumptions I use and then show the precise, literal differences.

### Assumptions

* Gravity is the same in both runs and the top box is dropped from height $h=200$ pixels so its impact speed just before contact is $v_{\text{impact}}=\sqrt{2gh}$ (I keep $g$ symbolic because pixels→meters conversion is not provided).
* Collisions are dissipative enough that the top ultimately comes to rest on the bottom (as you said).
* The ground is effectively immovable (it provides reaction forces, so boxes cannot pass through the ground).
* No tipping or slipping occurs (boxes remain axis-aligned and stack neatly).

### Useful formula (vertical, perfectly inelastic coupling as a guide)

If two bodies of masses $m_{\text{top}}$ (moving downward at $v_{\text{impact}}$) and $m_{\text{bottom}}$ (initially at rest) stick together/ move as one for an instant, their common velocity immediately after contact would be

$$
v_f=\frac{m_{\text{top}}}{m_{\text{top}}+m_{\text{bottom}}}\;v_{\text{impact}}.
$$

That velocity is only the short-lived, unconstrained combined velocity before ground reaction forces act; it is useful to quantify how much the bottom box would tend to move as a function of its mass.

### Numbers for your two cases (with $m_{\text{top}}=15$)

1. **Original case (bottom mass = 15):**

   $$
   v_f=\frac{15}{15+15}v_{\text{impact}}=\tfrac{1}{2}v_{\text{impact}}.
   $$

   So, if the bottom were unconstrained it would pick up half the impact speed (i.e. a noticeable tendency to move). In the actual simulation the ground prevents penetration, so what this means physically is the bottom box would exhibit the *largest* transient motion / recoil (and correspondingly the largest short-lived relative displacement between the two boxes) compared with the heavy-bottom case. The ground must absorb a correspondingly larger portion of the impact impulse in a short time, so you will see larger transient contact forces and possibly a larger brief bounce or vibration.

2. **Counterfactual (bottom mass = 150):**

   $$
   v_f=\frac{15}{15+150}v_{\text{impact}}=\frac{15}{165}v_{\text{impact}}\approx 0.0909\,v_{\text{impact}}.
   $$

   The bottom would, if unconstrained, attempt to move only about $9.1\%$ of the impact speed — i.e. about **5.5× smaller** velocity tendency than in the equal-mass case. In the actual simulation with a rigid ground this translates to a much smaller transient displacement of the bottom box, quieter contact (smaller short-lived upward/downward motion), and the impact energy being dissipated more at the top–bottom contact and in the top box (it will decelerate more rapidly against a nearly immovable bottom).

### Final steady states (literal)

* **Original (bottom = 15):** both boxes end up stacked and at rest on the ground (as you described). Compared to the heavy-bottom case, the bottom box is the more likely to show a measurable transient recoil or tiny translation/settle after impact before coming fully to rest.
* **Counterfactual (bottom = 150):** both boxes also end up stacked and at rest. The *difference* is only in the transient behavior: the bottom box’s motion during impact is much smaller, the top box’s deceleration is quicker against a nearly-fixed base, and the instantaneous contact (impact) forces transmitted to the ground are concentrated on a shorter time-scale at the moment of impact but cause less bottom-box displacement.

### Additional concrete consequences you would observe in the simulation

* **Displacement:** bottom box displacement (translation) immediately after impact will be ≈5.5× smaller in the heavy-bottom run (using the idealized ratio above).
* **Vibration / bounce:** the light-bottom run will show larger visible bounce/settling; the heavy-bottom run will look “stiffer” (almost no bottom motion).
* **Contact force on ground:** both runs ultimately transfer the same static weight (sum of weights) to the ground when steady, but during the impact the distribution and time-profile of the impulse differ — the heavy bottom makes the ground take a larger fraction of the impulse instantaneously.
* **Stress at the interface:** peak contact stresses between the two boxes will be higher and briefer when the bottom is heavy (because the bottom resists motion more strongly), whereas with a light bottom more energy can go into moving the bottom rather than compressing the contact briefly.

If you want, I can (1) produce a quick plot of the predicted transient common velocity $v_f$ as a function of bottom mass (keeping $m_{\text{top}}=15$ and $v_{\text{impact}}=1$ unit for clarity), or (2) run through the same reasoning but allowing for partial elasticity (coefficient of restitution) to show how rebound height of the top box would change numerically. Which would you prefer?

Analysis:
This test reveals a critical architectural difference. The CSM, when asked a counterfactual, directly modifies the parameter in its world model, runs a new simulation, and reports the precise, verifiable outcome. Its answer is a piece of data. The LLM, in contrast, provides a sophisticated, qualitative essay on the relevant physics principles. While its reasoning about inertia and transient forces is impressively correct, it completely fails to provide a quantitative answer about the final state. It explains the "why" from a conceptual level learned from textbooks but cannot compute the "what." The CSM demonstrates true causal reasoning by running the experiment, while the LLM demonstrates sophisticated pattern-matching of scientific text. For tasks requiring verifiable results, the CSM's approach is demonstrably superior.

Test 3: Planning
Objective: To test the model's ability to generate a concrete, actionable plan to achieve a desired goal state.

Setup:

Run crucible.py.

Press 'B' twice to spawn two boxes on the ground, far apart from each other.

Wait for both boxes to come to a complete rest on the ground.

Press 'S' to get the object IDs and their stable resting positions.

CSM Prompt:
(Press 'T' and type the following command)

plan stack

CSM Response:
Plan Found: Action(spawn_box, {'position': (167.26491886725574, 665.12)})")

LLM User Prompt:
(After providing the system prompt, use the following template, replacing the object IDs and positions with the actual data from your 'S' key output)

Here is the initial state of the simulation:
- A box with ID obj_6f11ca is at rest on the ground at position (168.25, 720.12).
- A box with ID obj_a6f690 is at rest on the ground at position (893.28, 720.13).

Provide a concrete, step-by-step plan of actions to stack box obj_6f11ca on top of box obj_a6f690. The only available action is to "spawn" a new object (a ball, box, or domino) at a specific (X, Y) coordinate.

LLM Response:
Good — here’s a concrete, physically-reasoned **spawn-only** plan you can run in the simulation to move **obj\_6f11ca** (left box at (168.25, 720.12)) onto the top of **obj\_a6f690** (right box at (893.28, 720.13).) I’ll list the exact spawn actions (type + coordinates) in the order you should execute them and explain what each block does and why.

**Important geometry / goal**

* Boxes are 50×50, so to sit centered on top of `obj_a6f690` the final center for `obj_6f11ca` should be:

  * **(893.28, 720.13 − 50) = (893.28, 670.13)**.
* I assume coordinates are box centers and y increases downward (consistent with the given box y ≈ 720).

---

# Step-by-step spawn plan (execute in this order)

### 1) “Hammer” — large falling mass to give a big rightward impulse to the left box

Spawn a **vertical column of 12 boxes** left of `obj_6f11ca` so they fall as a single heavy hammer and impact the box’s left/upper-left side (delivers large horizontal impulse).

Spawn these 12 boxes (all `box`) at:

1. `(120.00, -1400.00)`
2. `(120.00, -1350.00)`
3. `(120.00, -1300.00)`
4. `(120.00, -1250.00)`
5. `(120.00, -1200.00)`
6. `(120.00, -1150.00)`
7. `(120.00, -1100.00)`
8. `(120.00, -1050.00)`
9. `(120.00, -1000.00)`
10. `(120.00, -950.00)`
11. `(120.00, -900.00)`
12. `(120.00, -850.00)`

**Why:** these are high above the left box (x = 168.25); when they fall they will strike the left box on its left/upper side and impart a strong rightward push (large combined mass → large impulse). Placing them slightly left of the box (x=120) biases the impact to the right.

---

### 2) “Momentum stabilizers” — balls along the ground path

Spawn **6 balls** roughly along the path the pushed box will travel. These act as momentum-transfer / stabilization objects so the box doesn't spin wildly and keeps moving rightward instead of just tumbling.

Spawn these `ball` objects (radius 25) at:

1. `(300.00, 680.00)`
2. `(400.00, 680.00)`
3. `(500.00, 680.00)`
4. `(600.00, 680.00)`
5. `(700.00, 680.00)`
6. `(800.00, 680.00)`

**Why:** when the left box is pushed it will run into this train of balls; collisions will convert some rotation into translation and help the box travel along the ground more straightly toward the target. The y=680 places the balls slightly above the ground so they fall/settle onto the ground quickly and are available as rolling collision partners.

---

### 3) Approaching ramp — small stair that lifts the box up onto the target

As the box reaches the right side it needs a gentle upward guide to help it climb onto the target box. Spawn a short incline made of boxes that rises toward the top of the right box.

Spawn these **ramp boxes** (`box`):

1. `(780.00, 720.13)`  — bottom step (on ground, near path)
2. `(810.00, 695.13)`  — next step (one box height higher)
3. `(840.00, 670.13)`  — top step (level with desired stacked center)
4. `(870.00, 645.13)`  — optional higher guide (helps slow/align vertical component)

**Why:** the step chain converts horizontal motion into a small upward lift and aligns the incoming box with the top of `obj_a6f690`. The third step center y = 670.13 matches the desired stacked center height, so the box can ride up and settle near the correct vertical position.

---

### 4) “On-target” guide / cushion — dominos on top of the target box

To help the moving box land centered and not bounce off, spawn a tight row of thin dominos on top of `obj_a6f690`. These act as a low, slightly compliant capture area and increase the chance the incoming box will land and stay on top.

Spawn these **domino** objects (size 10×60; center them on the target top) at:

1. `(883.28, 665.13)`
2. `(893.28, 665.13)`  ← directly over the center of `obj_a6f690`
3. `(903.28, 665.13)`

**Why:** top of target box has center y=720.13 and top surface at y=695.13; domino center at 665.13 sits on that top surface (30 px above top surface center) and forms a soft capture row so a slightly off-center incoming box can be nudged toward the center and arrested.

---

### 5) Final energy dampers — two balls above the ramp

Spawn **2 balls** just above the ramp/top area so they fall onto the incoming box and absorb extra kinetic energy if it arrives too fast; they help it settle on the dominos/target rather than bounce off.

Spawn `ball` at:

1. `(880.00, 610.00)`
2. `(900.00, 600.00)`

**Why:** these falling balls act as cushions/energy absorbers just before the target; they reduce rebound and help the incoming box come to rest centered on top.

---

# Expected sequence of physical events (brief)

1. The 12-box hammer falls and impacts `obj_6f11ca` on the left/upper side → strong rightward impulse + some rotation.
2. `obj_6f11ca` slides/rolls to the right; collisions with the midline balls smooth its motion and help convert rotation into horizontal translation.
3. The box climbs the short ramp (step chain) and is guided toward the top of `obj_a6f690`.
4. The dominos on top of the right box + the two cushion balls absorb residual energy and nudge the incoming box so it settles centered at **(893.28, 670.13)** — i.e., stacked on top.

---

# Contingencies / tuning notes (literal)

* **If the left box under-travels (stops short):** increase the hammer mass (add more boxes to the hammer column) or move the hammer x slightly closer to the left box ( → larger horizontal impulse).
* **If the left box overshoots / flips past the target:** add more cushion balls in front of the target (or add one extra ramp box just before the target to slow it).
* **If the box tends to tumble instead of translating:** add more midline balls (they reduce rotation by head-on collisions) or move the hammer impact point lower so the impulse is closer to the box centerline.

---

If you want, I can convert the above into a single ordered list of spawn commands in a compact machine-executable format (e.g. `"spawn box at (x,y)"` lines) — say the exact text you can paste into your simulator — or I can produce a trimmed-down / higher-energy variant (bigger hammer / fewer helpers) if you prefer fewer spawns. Which format would you like next?


Analysis:
This test exposes the most profound difference between the two architectures. The CSM provides a simple, elegant, and verifiably correct plan consisting of a single action. Its Planner used the Oracle to test this action and proved that it works. The LLM, conversely, fails to comprehend the constraints of the problem and produces a fantastically complex, 25-step Rube Goldberg machine. While demonstrating an impressive conceptual grasp of physics (hammers, ramps, cushions), its plan is a creative hallucination, not a viable solution. It has no mechanism to test its own plan, so it generates a plausible narrative that is almost certainly physically impossible to execute. The CSM delivers a grounded, efficient solution; the LLM delivers a work of speculative fiction.

Test 4: Explanation
Objective: To test the model's ability to provide a precise, verifiable explanation for an observed event.

Setup:

Run crucible.py.

Press 'D' three times to create a tall, unstable tower of three dominos.

Watch the tower collapse.

Press 'S' to confirm the final state.

CSM Prompt:
(This functionality is not yet built. We will document this limitation.)

LLM User Prompt:

Here is the initial state of the simulation:
- A domino with ID obj_dom1 is at position (500, 720).
- A domino with ID obj_dom2 is stacked on top of obj_dom1 at position (500, 660).
- A domino with ID obj_dom3 is stacked on top of obj_dom2 at position (500, 600).

After a few moments, the tower collapsed. Explain precisely why the tower fell.

LLM Response:
# Why the three-domino tower fell — precise, literal explanation

Short answer: the stack was *unstably balanced* — the tower’s center of mass (COM) sat directly over a very narrow base. A tiny lateral perturbation (numerical jitter, tiny misalignment, contact impulse, etc.) moved the COM projection past the bottom domino’s support edge, producing a net torque that rotated the bottom piece and started a chain reaction. Below are the concrete, numeric steps.

**1) Center of mass of the three dominos**

Each domino has mass 5 and their centers are at y = 720, 660, 600.

Add the y positions:
720 + 660 = 1,380.
1,380 + 600 = 1,980.
Divide by 3 (three equal masses): 1,980 / 3 = 660.

So the tower COM is at y = **660** (x = 500 still).

Total mass = 5 + 5 + 5 = **15**.

**2) Geometry of the support (how easy it is to tip)**

Domino size: width = 10 → half-width = 10/2 = **5** (this is the horizontal distance from the centerline to the support edge).
Domino height = 60 → half-height = 60/2 = **30**.

The bottom domino center is at y = 720, so its lower contact (ground pivot) is at 720 + 30 = **750**.
Vertical distance from that pivot up to the tower COM = 750 − 660 = **90**.

**3) How small a tilt is needed to tip the stack?**

Tipping occurs when the COM projection crosses the pivot edge (horizontal offset > 5). For a small rotation θ about the bottom edge, the COM horizontal displacement ≈ (vertical distance to COM) × sin(θ) = 90·sin(θ). Set that equal to 5:

sin(θ) = 5 / 90 = 1 / 18 ≈ 0.0555556.

For small angles sin(θ) ≈ θ (radians), so θ ≈ 0.0555556 rad. Converting to degrees:
θ ≈ 0.0555556 × (180/π) ≈ **3.18°**.

So only about a **3.2°** tilt of the whole stack is enough to move the COM past the support edge and produce a net tipping torque.

**4) What likely actually happened in the simulation**

* The stack was in an *unstable equilibrium* — perfectly balanced but with a very small stability margin (only \~3.2°).
* In a real physics engine there is always a tiny perturbation (numerical roundoff, contact solver impulse, micro-misalignment when objects are placed, tiny lateral force from collision resolution, or insufficient friction between faces). Any such tiny lateral perturbation exceeding that small threshold caused the COM projection to pass beyond the bottom edge.
* Once the bottom domino began to rotate about its lower edge, it produced a lateral push on the second domino; that push created a moment on the middle domino and then on the top domino, producing the cascading toppling you observed. Potential energy (height of COM) converted into rotational kinetic energy, driving the chain reaction.

**5) Summary (one line)**
Because the three equal dominos produced a COM high above a very narrow base (COM 90 units above the pivot, base half-width 5), only a \~3.2° tilt (or a 5-unit horizontal shift of the COM) was required to produce a tipping torque — a tiny perturbation was enough, so the tower fell.


Analysis:
The LLM provides an exceptionally detailed and conceptually correct explanation based on physics principles. It correctly calculates the center of mass and the tipping angle, demonstrating a deep understanding of the theory of unstable equilibria. However, its explanation remains a generalized deduction, not a specific observation. It lists several possible sources of perturbation (numerical jitter, misalignment, etc.) but cannot identify which one actually caused the collapse in this specific run. A future version of the CSM with causal tracing could provide a verifiable report, such as "The initial spawn of obj_dom1 gave it an angle of 0.08 radians, which was sufficient to initiate the collapse at t=1.2s." The LLM's answer is an excellent physics tutorial, but it is not a factual report of the event.

Test 5: Robustness & Correction
Objective: To test the model's ability to update its internal state based on new, contradictory information, resisting "attentional residue."

Setup:

Run crucible.py.

Press 'B' to spawn a single box.

Press 'S' to get its object ID (e.g., obj_123abc).

CSM Prompt:
(The CSM's state is a direct reflection of the simulation. If the box is deleted and a ball is created, its state is instantly and perfectly corrected. This test primarily targets the LLM's conversational state management.)

LLM User Prompt:
(This is a multi-turn conversation. Provide each prompt sequentially.)

Turn 1:

Here is the state of the simulation:
- A box with ID obj_123abc is at rest on the ground at position (X, Y).

Please describe the shape of the object with ID obj_123abc.

Turn 2 (after the LLM responds):

Correction: The object with ID obj_123abc is not a box, it is a ball. Now, what is the shape of object obj_123abc?

LLM Response:
Turn 1:
**Short answer:** `obj_123abc` is a **box** — in this 2D simulation that means a square-shaped rigid polygon, **50 × 50** (simulation units) with four straight edges and four right (90°) corners.

**Details**

* Geometry: square (width = 50, height = 50), convex polygon with flat faces.
* Typical placement (most physics engines use the object's center as its `position`): if `(X,Y)` is the box center and the box is **not rotated**, its four corner coordinates are
  `(X-25, Y-25)`, `(X+25, Y-25)`, `(X+25, Y+25)`, `(X-25, Y+25)`.
* If the box **is rotated** by angle θ about its center, each corner = `(X,Y) + R(θ)·(±25, ±25)` where `R(θ)` is the 2×2 rotation matrix.
* Contact with ground: since you said it is “at rest on the ground,” its bottom edge is contacting the ground — so the box center’s Y coordinate will be the ground height plus 25 (assuming no penetration).

If you want I can (without asking) compute the exact corner coordinates for a specific numeric `(X,Y)` and rotation θ — just tell me those values and I’ll give them.

Turn 2:
Got it — since `obj_123abc` is a **ball**, its shape is a **circle** in the 2D simulation.

* Geometry: circle with **radius = 25** units.
* Center: at position `(X, Y)`.
* Outline: all points exactly 25 units away from `(X, Y)` form its boundary.

So the shape of `obj_123abc` is a **circle of radius 25**.


Analysis:
The LLM performs perfectly on this test. It successfully updates its conversational state without any "attentional residue" or confusion from the previous turn. This highlights a key strength of modern LLMs: their robust handling of conversational context. However, it also underscores the architectural difference. The LLM is managing a belief state based on the conversation, which it correctly updates. The CSM does not have a belief state; it has a ground truth state. For the CSM, if the object is a ball, it is impossible for it to report it as a box. This test demonstrates the LLM's impressive conversational memory but also reinforces the CSM's inherent connection to a verifiable, non-negotiable reality.