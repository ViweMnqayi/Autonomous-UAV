Autonomous UAV Simulation & Ground Control System

A software-based autonomous UAV (Unmanned Aerial Vehicle) simulation project designed to model drone flight, telemetry, flight control, environmental conditions, mission execution, and ground-control operations without requiring physical drone hardware.

The project is being developed as a realistic UAV simulation platform that can eventually incorporate flight dynamics, sensor simulation, autonomous navigation, machine learning, computer vision, replay systems, and hardware-in-the-loop integration.



## Project Overview

This project simulates a UAV operating in a virtual environment.

The simulator models important flight characteristics such as:

* Position and movement
* Velocity and acceleration
* Altitude
* Battery consumption
* Flight states
* Maximum altitude
* Maximum speed
* Takeoff and landing
* Flight duration
* Distance travelled
* Distance from home
* Target altitude
* Target speed
* Return-to-home behaviour
* Emergency stopping
* Wind and environmental effects
* Signal and communication status
* Mission execution
* Flight replay and telemetry history

The project also includes a FastAPI backend that exposes the UAV simulator through an API, allowing a Ground Control Station interface to control and monitor the simulated aircraft.



Current Architecture


                    PILOT / USER
                         │
                         ▼
                ┌─────────────────┐
                │  Ground Control │
                │       UI        │
                │  React + TS     │
                └────────┬────────┘
                         │
                    HTTP / API
                         │
                         ▼
                ┌─────────────────┐
                │     FastAPI     │
                │     Backend     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Mission Control │
                │ Flight Control  │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  UAV Simulator  │
                │  Drone Physics  │
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Telemetry       Terrain        Wind
          │              │              │
          ▼              ▼              ▼
      Signal       Emergency       Replay
      Monitor       Handling        System
                         │
                         ▼
                Ground Control UI


Technology Stack

Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

Simulation

* Python
* Object-oriented programming
* Flight-control logic
* Numerical calculations
* Environmental simulation
* Mission execution
* Telemetry generation

 Frontend

* React
* TypeScript
* Vite
* CSS
Development

* Git
* GitHub
* Visual Studio Code

Planned Technologies

The project may later incorporate:

* NumPy
* Pandas
* Matplotlib
* Plotly
* Scikit-learn
* PyTorch
* OpenCV
* Three.js
* React Three Fiber
* SQLite
* ROS 2
* PX4 / ArduPilot SITL



 Project Structure


autonomous-uav/
│
├── backend/
│   └── main.py
│
├── simulator/
│   ├── core/
│   │   ├── drone.py
│   │   ├── flight_controller.py
│   │   ├── terrain.py
│   │   ├── wind.py
│   │   ├── signal.py
│   │   ├── replay.py
│   │   ├── mission_controller.py
│   │   └── emergency.py
│   │
│   └── main.py
│
├── frontend/
│   └── src/
│       └── App.tsx
│
├── ml/
│
├── data/
│
├── docs/
│
├── tests/
│
├── .gitignore
└── README.md
```

Core Simulation Modules

drone.py

Contains the main UAV model, including:

* Position
* Velocity
* Acceleration
* Altitude
* Battery
* Flight state
* Flight statistics
* Home position
* Movement updates

flight_controller.py

Manages flight behaviour and control commands, including:

* Takeoff
* Landing
* Altitude control
* Speed control
* Directional movement
* Deceleration
* Return-to-home behaviour
* Hold and stop commands

terrain.py

Provides terrain and ground-environment support, including:

* Ground elevation
* Terrain height checks
* Ground collision prevention
* Altitude reference calculations
* Future support for more complex environments

wind.py

Simulates environmental wind conditions, including:

* Wind direction
* Wind speed
* Environmental movement effects
* Future support for variable and dynamic wind

signal.py

Represents communication and signal conditions between the UAV and the ground-control system, including:

* Signal strength
* Connection status
* Communication degradation
* Future support for signal loss and recovery behaviour

replay.py

Supports flight-history and telemetry replay functionality, including:

* Recording telemetry
* Storing flight events
* Reviewing previous flights
* Future playback controls and visualisation

mission_controller.py

Provides a foundation for autonomous mission execution, including:

* Mission states
* Mission commands
* Waypoint support
* Mission progress
* Future autonomous route planning

emergency.py

Handles emergency-related flight behaviour, including:

* Emergency stop
* Emergency state management
* Safety responses
* Future emergency landing and failsafe logic


Current UAV Simulation

The simulated UAV currently supports:

Flight States


LANDED
TAKING_OFF
FLYING
LANDING


Additional emergency, mission, signal, and replay states may be used by the supporting simulator modules as the system develops.

Flight Operations

* Takeoff
* Controlled altitude changes
* Horizontal movement
* Speed control
* Landing
* Return to home
* Emergency stop
* Hold and stop movement
* Mission-control foundations
* Telemetry recording
* Environmental simulation foundations

Flight Constraints

The simulator applies limits to the aircraft, including:

* Maximum altitude
* Maximum horizontal speed
* Maximum vertical speed
* Ground collision prevention
* Controlled landing
* Battery consumption
* Environmental effects
* Emergency handling

The flight controller uses acceleration and deceleration rather than instantly changing the UAV's velocity.



Environmental and Support Systems

The simulator is being expanded beyond basic movement and flight-state logic.

Terrain

Terrain support allows the simulator to maintain a ground reference and prevent the UAV from moving below the simulated surface.

Wind

Wind support provides a foundation for modelling environmental forces that can affect UAV movement and flight performance.

Signal Monitoring

Signal support allows the system to represent the communication link between the UAV and the Ground Control Station.

 Emergency Handling

Emergency support provides a dedicated location for safety-related behaviour, emergency stops, and future failsafe procedures.

Mission Control

Mission-control support provides the foundation for waypoint missions, autonomous commands, and future path-planning features.

Flight Replay

Replay support allows telemetry and flight events to be recorded for later analysis, debugging, visualisation, and machine-learning dataset generation.

Example Simulation

A typical simulated flight currently follows a sequence similar to:

Takeoff
   ↓
Climb
   ↓
Reach target altitude
   ↓
Fly forward
   ↓
Environmental effects applied
   ↓
Change direction
   ↓
Return or hold
   ↓
Controlled landing
   ↓
Landed


Example telemetry:


State: FLYING
Position: X=20.0m Y=0.0m Z=21.37m
Velocity: X=5.0m/s Y=0.0m/s Z=0.0m/s
Battery: 99%
Signal: CONNECTED




Backend API

The FastAPI backend exposes endpoints for controlling and monitoring the UAV.

System


GET /api/health


Checks whether the UAV API is running.

Telemetry


GET /api/drone/status


Returns the current UAV status.

Flight Control


POST /api/drone/takeoff
POST /api/drone/land
POST /api/drone/return-home
POST /api/drone/emergency-stop


Flight Parameters


POST /api/drone/altitude
POST /api/drone/speed

 Movement


POST /api/drone/move
POST /api/drone/stop


Future API Areas

The backend may later expose endpoints for:


GET  /api/drone/telemetry
GET  /api/drone/replay
POST /api/drone/missions
POST /api/drone/waypoints
GET  /api/drone/signal
GET  /api/drone/environment
POST /api/drone/emergency-land




Running the Project

1. Clone the repository


git clone https://github.com/YOUR-USERNAME/autonomous-uav.git
cd autonomous-uav
`
2. Create the Python virtual environment


python -m venv .venv


Activate it on Windows:

cmd
.venv\Scripts\activate

3. Install backend dependencies


pip install fastapi uvicorn


 4. Run the simulator


python simulator/main.py


5. Run the FastAPI backend

From the project root:

uvicorn backend.main:app --reload


The API will be available at:

http://127.0.0.1:8000


FastAPI documentation:


http://127.0.0.1:8000/docs


6. Run the frontend

Open another terminal:

cmd
cd frontend
npm install
npm run dev


The React application will normally be available at:


http://localhost:5173




Development Roadmap

This project is being developed progressively.

Phase 1 — UAV Core Simulation

* [x] Drone model
* [x] Position tracking
* [x] Velocity
* [x] Acceleration
* [x] Altitude limits
* [x] Speed limits
* [x] Battery simulation
* [x] Flight states
* [x] Takeoff
* [x] Landing
* [x] Horizontal movement
* [x] Return-to-home foundation
* [x] Emergency stop
* [x] Flight statistics

Phase 2 — Ground Control System

* [x] FastAPI backend
* [x] UAV telemetry endpoint
* [x] Flight-control endpoints
* [x] React frontend foundation
* [x] Backend/frontend communication
* [x] Live telemetry display
* [x] Flight controls

Phase 3 — Simulation Support Systems

* [x] Terrain module foundation
* [x] Wind module foundation
* [x] Signal module foundation
* [x] Replay module foundation
* [x] Mission-controller foundation
* [x] Emergency-handling foundation
* [ ] Connect all support modules to the main simulation loop
* [ ] Add persistent telemetry storage
* [ ] Add automated tests for support modules

Phase 4 — Flight Visualization

* [ ] Camera-following flight view
* [ ] Ground environment
* [ ] Flight trajectory
* [ ] Waypoints
* [ ] Improved UAV visualization
* [ ] 3D environment
* [ ] Three.js / React Three Fiber integration
* [ ] Replay visualisation

Phase 5 — Realistic Flight Dynamics

[ ] Thrust model
[ ] Gravity
[ ] Drag
[ ] Inertia
[ ] Roll
[ ] Pitch
[ ] Yaw
[ ] More realistic acceleration
[ ] More realistic battery model
[ ] Wind-force integration
[ ] Terrain-aware altitude calculations

Phase 6 — Sensor Simulation

[ ] GPS simulation
[ ] IMU simulation
[ ] Barometer
[ ] Magnetometer
[ ] Sensor noise
[ ] Sensor fusion
[ ] Kalman filtering

Phase 7 — Autonomous Flight

[ ] PID controllers
[ ] Autonomous altitude control
[ ] Autonomous navigation
[ ] Waypoint missions
[ ] Path planning
[ ] Obstacle avoidance
[ ] Return-to-home logic
[ ] Mission control
[ ] Mission interruption and recovery
[ ] Signal-loss failsafe behaviour

Phase 8 — Machine Learning

 [ ] Flight-data generation
 [ ] Telemetry dataset
 [ ] Anomaly detection
 [ ] Flight-performance analysis
 [ ] Predictive models
 [ ] ML-based fault detection
 [ ] Replay-based training data generation

Phase 9 — Computer Vision

 [ ] Camera simulation
 [ ] Object detection
 [ ] Obstacle detection
 [ ] Landing-zone detection
 [ ] Computer-vision navigation



Future Flight Data

The simulator will eventually generate datasets containing telemetry such as:

timestamp
x
y
z
velocity_x
velocity_y
velocity_z
acceleration_x
acceleration_y
acceleration_z
altitude
speed
battery
state
distance_travelled
distance_from_home
wind_speed
wind_direction
signal_strength
mission_state
emergency_state


These datasets can later be used for:

Machine learning
Anomaly detection
Flight analysis
Predictive maintenance research
Controller evaluation
Simulation experiments
Mission-performance analysis
Replay and debugging



Project Goals

The long-term goal is to develop a software-based UAV platform that combines:


Flight Simulation
       +
Flight Control
       +
Ground Control
       +
Telemetry
       +
Terrain
       +
Wind
       +
Signal Monitoring
       +
Emergency Handling
       +
Mission Control
       +
Flight Replay
       +
Sensors
       +
Autonomous Navigation
       +
Machine Learning
       +
Computer Vision


The project is intended to progress from a basic flight simulator into a more advanced autonomous UAV research and development environment.



Disclaimer

This project is a software simulation and educational/research project. It does not directly control a physical UAV.

Any future integration with real UAV hardware would require appropriate hardware interfaces, safety mechanisms, flight-controller integration, testing procedures, and compliance with applicable aviation regulations.



Author

Viwe Mnqayi

Information Technology / ICT Student

This project is being developed as part of a personal software engineering, UAV simulation, and artificial intelligence portfolio.

