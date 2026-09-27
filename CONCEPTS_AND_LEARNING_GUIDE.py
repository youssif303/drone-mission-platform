# Drone Mission Planning & Perception Platform
# Learning Guide — Concepts You Need to Know
# =============================================

# This document covers every technical concept used in this project.
# Study these topics to fully understand the codebase and be able
# to explain everything in job interviews.


# ============================================================
# PART 1: COMPUTER VISION & PERCEPTION
# ============================================================

# --------------------------------------------------------------
# 1.1 Object Detection (YOLOv8)
# --------------------------------------------------------------
#
# WHAT IS IT?
#   Object detection = finding objects in an image and drawing
#   bounding boxes around them with class labels.
#
#   Input:  A single image (e.g., 640x640 pixels)
#   Output: List of detections, each with:
#           - class_name: "car", "person", "truck"
#           - bounding_box: (x1, y1, x2, y2) — top-left and bottom-right corners
#           - confidence: 0.0 to 1.0 (how sure the model is)
#
# HOW YOLO WORKS (simplified):
#   1. Image is divided into a grid (e.g., 80x80 cells)
#   2. Each cell predicts: "Is there an object centered here?"
#   3. If yes → predict bounding box coordinates + class probabilities
#   4. Non-Maximum Suppression (NMS) removes duplicate overlapping boxes
#   5. All done in ONE forward pass (that's why it's "You Only Look Once")
#
# KEY TERMS:
#   - mAP (mean Average Precision): main accuracy metric for detection
#   - IoU (Intersection over Union): measures overlap between two boxes
#         IoU = Area_of_Overlap / Area_of_Union
#         IoU > 0.5 = "good match", IoU = 1.0 = "perfect overlap"
#   - Confidence threshold: ignore detections below this (e.g., 0.35)
#   - NMS (Non-Maximum Suppression): if two boxes overlap a lot (high IoU),
#     keep only the one with higher confidence
#   - Anchor-free detection: YOLOv8 doesn't use predefined anchor boxes
#     (unlike older versions), it directly predicts box center + size
#
# INFERENCE FORMATS:
#   - PyTorch (.pt): native format, needs PyTorch installed
#   - ONNX (.onnx): cross-platform, runs with ONNX Runtime (faster, no PyTorch needed)
#   - TensorRT (.engine): NVIDIA-optimized, fastest on GPU
#
# RESOURCES:
#   - Ultralytics YOLOv8 docs: https://docs.ultralytics.com/
#   - Original YOLO paper concept: https://arxiv.org/abs/1506.02640
#   - VisDrone dataset (drone-specific): https://github.com/VisDrone/VisDrone-Dataset


# --------------------------------------------------------------
# 1.2 Multi-Object Tracking (MOT)
# --------------------------------------------------------------
#
# WHAT IS IT?
#   Object detection works frame-by-frame. But we need to know:
#   "Is this car in Frame 5 the SAME car that was in Frame 4?"
#   Tracking assigns a persistent ID to each object across frames.
#
# HOW OUR TRACKER WORKS (IoU-based, similar to SORT/ByteTrack):
#
#   Frame N:  Detections = [det_A, det_B, det_C]
#   Existing: Tracks    = [track_1, track_2]
#
#   Step 1: Build COST MATRIX (IoU between every track and detection)
#           ┌──────────┬────────┬────────┬────────┐
#           │          │ det_A  │ det_B  │ det_C  │
#           ├──────────┼────────┼────────┼────────┤
#           │ track_1  │  0.85  │  0.02  │  0.00  │
#           │ track_2  │  0.01  │  0.72  │  0.03  │
#           └──────────┴────────┴────────┴────────┘
#
#   Step 2: HUNGARIAN ALGORITHM finds optimal assignment
#           Result: track_1 ↔ det_A, track_2 ↔ det_B
#           (maximizes total IoU)
#
#   Step 3: UPDATE matched tracks (new position from detection)
#
#   Step 4: CREATE new track for unmatched det_C → track_3
#
#   Step 5: AGE unmatched tracks (if a track has no match for
#           too many frames → delete it)
#
# TRACK LIFECYCLE:
#   tentative → confirmed → lost → deleted
#   - tentative: just created, not yet reliable (needs min_hits matches)
#   - confirmed: matched in enough consecutive frames, this is real
#   - lost: hasn't been matched for a few frames (might be occluded)
#   - deleted: lost for too long (max_age frames), remove permanently
#
# VELOCITY ESTIMATION:
#   velocity = (current_bbox_center - previous_bbox_center) / dt
#   This gives pixel velocity. Combined with geo-referencing,
#   we get real-world speed in m/s.
#
# KEY TERMS:
#   - MOTA (Multiple Object Tracking Accuracy): main tracking metric
#   - ID Switch: when the tracker accidentally swaps two objects' IDs
#   - Occlusion: when one object hides behind another
#   - Re-identification (Re-ID): recognizing the same object after it
#     disappears and reappears (advanced, not used in our simple tracker)
#
# RESOURCES:
#   - SORT paper (simple, foundational): https://arxiv.org/abs/1602.00763
#   - ByteTrack paper: https://arxiv.org/abs/2110.06864
#   - Hungarian Algorithm explained: https://en.wikipedia.org/wiki/Hungarian_algorithm


# --------------------------------------------------------------
# 1.3 VisDrone Dataset
# --------------------------------------------------------------
#
# WHAT IS IT?
#   A large-scale dataset of images/videos captured by drones.
#   Contains annotations for 10 object classes:
#   pedestrian, person, car, van, bus, truck, motor, bicycle,
#   awning-tricycle, tricycle
#
# WHY USE IT?
#   - Regular detection models (trained on COCO) work on ground-level photos
#   - Drone footage is VERY different: objects are tiny, viewed from above
#   - Fine-tuning YOLOv8 on VisDrone makes detection much better for our use case
#
# STATISTICS:
#   - 10,209 images (train + val + test)
#   - ~540,000 annotated bounding boxes
#   - Multiple cities, altitudes, weather conditions


# ============================================================
# PART 2: GEO-REFERENCING (Camera Math)
# ============================================================

# --------------------------------------------------------------
# 2.1 Pinhole Camera Model
# --------------------------------------------------------------
#
# The pinhole camera model describes how 3D points in the world
# project onto a 2D image.
#
# INTRINSIC MATRIX K:
#   K = | fx   0   cx |     fx, fy = focal length (pixels)
#       |  0  fy   cy |     cx, cy = principal point (image center)
#       |  0   0    1 |
#
# PROJECTION (3D → 2D):
#   [u]       [X]
#   [v] = K · [Y]  / Z     (u,v) = pixel coordinates
#   [1]       [Z]           (X,Y,Z) = 3D point in camera frame
#
# BACK-PROJECTION (2D → 3D ray):
#   [X]         [u]
#   [Y] = K⁻¹ · [v]        This gives a RAY direction, not a point
#   [Z]         [1]         (we need additional info to get depth)
#
# FROM FIELD OF VIEW (FOV):
#   If you know the camera's horizontal FOV (e.g., 90°):
#   fx = (image_width / 2) / tan(fov_horizontal / 2)
#   fy = fx  (assuming square pixels)
#   cx = image_width / 2
#   cy = image_height / 2
#
# RESOURCES:
#   - OpenCV Camera Calibration: https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html
#   - Multiple View Geometry (textbook, advanced): Hartley & Zisserman


# --------------------------------------------------------------
# 2.2 Coordinate Frame Transformations
# --------------------------------------------------------------
#
# We deal with FOUR coordinate frames:
#
# 1. IMAGE FRAME (2D)
#    - Origin: top-left corner of image
#    - x → right, y → down
#    - Units: pixels
#
# 2. CAMERA FRAME (3D)
#    - Origin: camera optical center (on the drone)
#    - z → forward (out of camera), x → right, y → down
#    - Units: meters
#
# 3. DRONE/LOCAL FRAME (3D)
#    - Origin: drone position
#    - x → North, y → East, z → Down (NED convention)
#    - Units: meters
#    - Related to camera frame by GIMBAL ROTATION
#
# 4. WORLD/GPS FRAME
#    - Latitude, Longitude, Altitude
#    - Units: degrees (WGS84 ellipsoid)
#
# TRANSFORMATION CHAIN:
#   Image (pixels) → Camera (3D ray) → Drone/Local (3D ray rotated) → GPS
#
#   Step 1: pixel → camera ray:    ray = K⁻¹ · [u, v, 1]ᵀ
#   Step 2: apply gimbal rotation:  ray_world = R(pitch) · ray
#   Step 3: ray-ground intersection: find where ray hits z=0
#   Step 4: rotate by heading:      apply drone heading to get N/E offset
#   Step 5: offset → GPS:           add meter offset to drone GPS position


# --------------------------------------------------------------
# 2.3 Ray-Ground Intersection
# --------------------------------------------------------------
#
# The drone is at altitude h (meters above ground).
# We assume flat ground (z = 0 plane).
# The camera ray direction is (rx, ry, rz) in world frame.
#
# Parametric ray equation:
#   P(t) = drone_position + t × ray_direction
#
# At ground level (z = 0):
#   0 = h + t × rz
#   t = -h / rz
#
# Ground intersection point:
#   x_ground = t × rx   (meters east of drone)
#   y_ground = t × ry   (meters north of drone)
#
# IMPORTANT: This only works if rz < 0 (ray points downward).
# If rz >= 0, the ray points up/horizontal and never hits the ground.


# --------------------------------------------------------------
# 2.4 GPS Coordinate Math
# --------------------------------------------------------------
#
# Converting between meters and GPS degrees:
#
# LATITUDE:
#   1 degree of latitude ≈ 111,320 meters (roughly constant everywhere)
#   delta_lat = meters_north / 111320
#
# LONGITUDE:
#   1 degree of longitude varies with latitude:
#   1 degree ≈ 111,320 × cos(latitude) meters
#   delta_lon = meters_east / (111320 × cos(lat_radians))
#
# HAVERSINE FORMULA (distance between two GPS points):
#   a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
#   c = 2 × atan2(√a, √(1−a))
#   distance = R × c   (R = 6,371,000 m = Earth's radius)
#
# BEARING (direction from point A to point B):
#   θ = atan2(sin(Δlon)×cos(lat2),
#             cos(lat1)×sin(lat2) − sin(lat1)×cos(lat2)×cos(Δlon))
#   bearing = θ in degrees (0° = North, 90° = East)
#
# RESOURCES:
#   - Haversine formula: https://en.wikipedia.org/wiki/Haversine_formula
#   - Coordinate systems in robotics: https://www.ros.org/reps/rep-0103.html


# ============================================================
# PART 3: BACKEND ENGINEERING
# ============================================================

# --------------------------------------------------------------
# 3.1 REST API (FastAPI)
# --------------------------------------------------------------
#
# REST = Representational State Transfer
# A standard way for clients (frontend) to communicate with servers (backend)
#
# HTTP METHODS:
#   GET    /api/missions       → List all missions (READ)
#   POST   /api/missions       → Create a new mission (CREATE)
#   GET    /api/missions/5     → Get mission with id=5 (READ one)
#   PUT    /api/missions/5     → Update mission 5 (UPDATE)
#   DELETE /api/missions/5     → Delete mission 5 (DELETE)
#
# FastAPI ADVANTAGES:
#   - Auto-generates Swagger/OpenAPI docs at /docs
#   - Built-in data validation with Pydantic
#   - Async support (important for WebSocket + DB)
#   - Type hints everywhere → fewer bugs
#
# EXAMPLE:
#   @router.post("/api/missions")
#   async def create_mission(data: MissionCreate, db: AsyncSession):
#       mission = MissionDB(**data.dict())
#       db.add(mission)
#       await db.commit()
#       return MissionResponse.from_orm(mission)
#
# RESOURCES:
#   - FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/
#   - HTTP Methods: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods


# --------------------------------------------------------------
# 3.2 WebSocket (Real-Time Streaming)
# --------------------------------------------------------------
#
# HTTP is request-response: client asks → server responds → connection closes.
# For real-time data (10-15 frames per second), this is too slow.
#
# WebSocket = persistent bidirectional connection:
#   1. Client opens connection: ws://localhost:8000/ws/detections
#   2. Connection stays open
#   3. Server pushes data whenever it has new data
#   4. Client receives instantly (no polling, no delays)
#
# WE USE 3 WebSocket CHANNELS:
#   /ws/video-feed      → Base64 JPEG frames (drone camera)
#   /ws/detections      → JSON array of GeoDetection objects
#   /ws/drone-telemetry → JSON DroneState (position, speed, battery)
#
# EXAMPLE (FastAPI):
#   @app.websocket("/ws/detections")
#   async def detections_ws(websocket: WebSocket):
#       await websocket.accept()
#       while True:
#           data = get_latest_detections()
#           await websocket.send_json(data)
#           await asyncio.sleep(1/15)  # 15 FPS
#
# RESOURCES:
#   - WebSocket Protocol: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
#   - FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/


# --------------------------------------------------------------
# 3.3 Async Python (asyncio)
# --------------------------------------------------------------
#
# WHY ASYNC?
#   Our backend does many things simultaneously:
#   - Serve HTTP requests
#   - Stream WebSocket data to multiple clients
#   - Read from database
#   - Process perception data
#
#   With synchronous code, each task blocks the others.
#   With async code, tasks cooperate: when one waits (I/O),
#   another runs.
#
# KEY CONCEPTS:
#   async def my_function():     # declares an async function
#       result = await db.execute(query)  # "await" = pause here,
#                                          # let other tasks run,
#                                          # resume when result is ready
#
#   asyncio.sleep(0.1)  # non-blocking sleep (other tasks can run)
#   time.sleep(0.1)     # BLOCKING sleep (everything stops!) — NEVER use in async
#
# RESOURCES:
#   - Real Python Async: https://realpython.com/async-io-python/


# --------------------------------------------------------------
# 3.4 SQLAlchemy ORM (Database)
# --------------------------------------------------------------
#
# ORM = Object-Relational Mapping
# Instead of writing raw SQL, you define Python classes that map to DB tables.
#
# EXAMPLE:
#   class MissionDB(Base):
#       __tablename__ = "missions"
#       id = Column(Integer, primary_key=True)
#       name = Column(String, nullable=False)
#       status = Column(String, default="planned")
#       waypoints = relationship("WaypointDB", back_populates="mission")
#
#   # Create a mission:
#   mission = MissionDB(name="Urban Patrol")
#   session.add(mission)
#   await session.commit()
#
#   # Query missions:
#   result = await session.execute(select(MissionDB).where(MissionDB.status == "active"))
#   missions = result.scalars().all()
#
# WE USE:
#   - SQLite (development) — file-based, no server needed
#   - aiosqlite — async SQLite driver
#   - Could upgrade to PostgreSQL for production
#
# RESOURCES:
#   - SQLAlchemy 2.0 Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/


# --------------------------------------------------------------
# 3.5 Pydantic (Data Validation)
# --------------------------------------------------------------
#
# Pydantic models validate and serialize data automatically.
# Used for: API request/response bodies, WebSocket messages, config.
#
# EXAMPLE:
#   class GeoDetection(BaseModel):
#       track_id: int
#       class_name: str
#       latitude: float        # auto-validated as float
#       longitude: float
#       speed_mps: float
#       confidence: float = Field(ge=0, le=1)  # must be 0-1
#       timestamp: datetime
#
#   # FastAPI auto-validates incoming JSON against this schema
#   # Invalid data → automatic 422 error response
#
# RESOURCES:
#   - Pydantic V2 Docs: https://docs.pydantic.dev/latest/


# ============================================================
# PART 4: FRONTEND ENGINEERING
# ============================================================

# --------------------------------------------------------------
# 4.1 React (UI Framework)
# --------------------------------------------------------------
#
# React = JavaScript library for building user interfaces
# Core concepts:
#
# COMPONENTS:
#   function DroneStatus({ droneState }) {
#     return (
#       <div>
#         <span>Altitude: {droneState.altitude_m}m</span>
#         <span>Speed: {droneState.speed_mps} m/s</span>
#         <span>Battery: {droneState.battery_percent}%</span>
#       </div>
#     );
#   }
#
# HOOKS:
#   - useState: local component state
#   - useEffect: side effects (API calls, subscriptions)
#   - useRef: direct DOM access (for Canvas drawing)
#   - Custom hooks: useWebSocket, useDetections (our own)
#
# STATE MANAGEMENT (Zustand):
#   - Lightweight global state store
#   - Shared data between components (active mission, selected track)
#
# RESOURCES:
#   - React Official: https://react.dev/learn
#   - TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/


# --------------------------------------------------------------
# 4.2 React-Leaflet (Interactive Maps)
# --------------------------------------------------------------
#
# Leaflet = JavaScript library for interactive maps
# React-Leaflet = React wrapper for Leaflet
#
# WE USE IT FOR:
#   - Showing the map with satellite/dark tiles
#   - Drone position marker (moves in real-time)
#   - Detection markers (colored pins for each tracked object)
#   - Track trails (polylines showing object movement history)
#   - Waypoint markers (mission plan)
#   - Zone overlays (restricted areas — polygons on the map)
#
# EXAMPLE:
#   <MapContainer center={[48.13, 11.58]} zoom={15}>
#     <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
#     <Marker position={[droneState.lat, droneState.lon]}>
#       <Popup>Drone — Alt: {droneState.altitude_m}m</Popup>
#     </Marker>
#     {detections.map(det => (
#       <CircleMarker center={[det.latitude, det.longitude]}
#                     color={det.class_name === 'person' ? 'red' : 'orange'} />
#     ))}
#   </MapContainer>
#
# RESOURCES:
#   - React-Leaflet: https://react-leaflet.js.org/
#   - Leaflet: https://leafletjs.com/


# --------------------------------------------------------------
# 4.3 HTML Canvas API (Video + Detection Overlays)
# --------------------------------------------------------------
#
# The Canvas API lets you draw graphics programmatically.
# We use it to:
#   1. Render drone camera frames (received as base64 JPEG via WebSocket)
#   2. Draw bounding boxes on top of the video
#   3. Add class labels and confidence text
#
# EXAMPLE:
#   const canvas = canvasRef.current;
#   const ctx = canvas.getContext('2d');
#
#   // Draw video frame
#   const img = new Image();
#   img.src = `data:image/jpeg;base64,${frameBase64}`;
#   img.onload = () => ctx.drawImage(img, 0, 0);
#
#   // Draw bounding box
#   ctx.strokeStyle = 'red';
#   ctx.lineWidth = 2;
#   ctx.strokeRect(x1, y1, width, height);
#
#   // Draw label
#   ctx.fillStyle = 'red';
#   ctx.fillText(`Person #3 (87%)`, x1, y1 - 5);
#
# RESOURCES:
#   - MDN Canvas: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API


# --------------------------------------------------------------
# 4.4 TailwindCSS (Styling)
# --------------------------------------------------------------
#
# Utility-first CSS framework. Instead of writing CSS files,
# you add classes directly to HTML elements.
#
# EXAMPLE:
#   <div className="bg-gray-900 text-green-400 p-4 rounded-lg border border-gray-700">
#     <h2 className="text-xl font-bold mb-2">Drone Status</h2>
#     <span className="font-mono text-sm">Alt: 50m</span>
#   </div>
#
# OUR THEME: Dark military/tactical look
#   - Background: #0a0f1a (very dark blue)
#   - Text: gray-100/gray-300
#   - Accents: green-500 (status), amber-500 (warnings), red-500 (alerts)
#   - Monospace font for data values
#
# RESOURCES:
#   - TailwindCSS: https://tailwindcss.com/docs


# ============================================================
# PART 5: MISSION PLANNING & DRONE CONTROL
# ============================================================

# --------------------------------------------------------------
# 5.1 Waypoint Navigation
# --------------------------------------------------------------
#
# A mission = an ordered list of GPS waypoints.
# The drone flies to each waypoint in sequence.
#
# LOGIC:
#   1. Drone starts at waypoint 0
#   2. Fly toward current waypoint
#   3. When distance < threshold (e.g., 5 meters) → "waypoint reached"
#   4. Advance to next waypoint
#   5. When all waypoints reached → mission complete
#
# WAYPOINT STRUCTURE:
#   Waypoint = (latitude, longitude, altitude)
#
# DISTANCE CHECK:
#   distance = haversine(drone_lat, drone_lon, waypoint_lat, waypoint_lon)
#   if distance < 5.0:  # meters
#       advance_to_next_waypoint()


# --------------------------------------------------------------
# 5.2 Search Patterns
# --------------------------------------------------------------
#
# Pre-defined flight patterns for systematic area coverage:
#
# GRID (Lawn-mower):
#   →→→→→→→→→→→
#               ↓
#   ←←←←←←←←←←←
#   ↓
#   →→→→→→→→→→→
#   Best for: complete area survey
#
# SPIRAL:
#       ┌──→──┐
#       │  ↗  ↓
#       │ ●   ↓    (● = center)
#       │     ↓
#       └──←──┘
#   Best for: focused search from a point of interest
#
# PERIMETER:
#       ╭──→──╮
#       │     │
#       ↑  ●  ↓    (● = center, circle around it)
#       │     │
#       ╰──←──╯
#   Best for: border patrol, facility perimeter security


# ============================================================
# PART 6: DEVOPS & DEPLOYMENT
# ============================================================

# --------------------------------------------------------------
# 6.1 Docker
# --------------------------------------------------------------
#
# Docker packages your application into a "container" — a lightweight,
# standalone unit that includes code + dependencies + runtime.
#
# WHY?
#   - "It works on my machine" → "It works on EVERY machine"
#   - Recruiters can run your project with ONE command
#
# OUR SETUP:
#   docker-compose.yml defines 2 services:
#   - backend: Python 3.11 + FastAPI + all perception code
#   - frontend: Node 20 (build) → Nginx (serve static files)
#
# ONE COMMAND TO RUN EVERYTHING:
#   docker compose up --build
#   → Backend at http://localhost:8000
#   → Frontend at http://localhost:3000
#
# RESOURCES:
#   - Docker Getting Started: https://docs.docker.com/get-started/
#   - Docker Compose: https://docs.docker.com/compose/


# --------------------------------------------------------------
# 6.2 CI/CD (GitHub Actions)
# --------------------------------------------------------------
#
# CI = Continuous Integration
# Every time you push code to GitHub, automated checks run:
#   1. Lint Python code (ruff) → catch style issues
#   2. Run pytest → catch bugs
#   3. Build frontend (npm run build) → catch TypeScript errors
#
# If any check fails → you see a red ❌ on your GitHub commit.
# If all pass → green ✅
#
# This shows recruiters you follow professional engineering practices.
#
# RESOURCES:
#   - GitHub Actions: https://docs.github.com/en/actions


# ============================================================
# PART 7: INTERVIEW PREPARATION
# ============================================================

# Common interview questions this project prepares you for:

# Q: "How does object detection work?"
# A: YOLO divides the image into a grid, each cell predicts bounding boxes
#    and class probabilities in a single forward pass. We use YOLOv8 with
#    ONNX Runtime for cross-platform deployment.

# Q: "How do you track objects across frames?"
# A: We use an IoU-based tracker similar to SORT. We compute an IoU cost matrix
#    between existing tracks and new detections, solve the assignment problem
#    with the Hungarian algorithm, and manage track lifecycles
#    (tentative → confirmed → lost → deleted).

# Q: "How do you convert pixel coordinates to GPS?"
# A: Using the pinhole camera model, we back-project the detection's pixel center
#    into a 3D ray in camera frame, apply the gimbal rotation, intersect the ray
#    with the ground plane at the drone's altitude, rotate by the drone's heading
#    to get north/east offset in meters, then convert meters to GPS deltas
#    using latitude-dependent scaling.

# Q: "How do you handle real-time data streaming?"
# A: We use WebSockets for persistent bidirectional connections. The backend pushes
#    annotated video frames, geo-referenced detections, and drone telemetry
#    at 10-15 FPS. The React frontend receives these via custom hooks and updates
#    the map, video canvas, and data panels in real-time.

# Q: "How would you deploy this to production?"
# A: Docker Compose for local deployment. For cloud: frontend on Vercel/Netlify,
#    backend on Railway/Render, with a pre-recorded demo mode that replays
#    recorded scenarios so the demo works without a live drone or simulator.

# Q: "What would you improve with more time?"
# A: 1) Use BEVFormer for proper BEV perception instead of simple projection,
#    2) Add Re-ID features to the tracker for better identity persistence,
#    3) Use terrain elevation data instead of flat-ground assumption,
#    4) Add TensorRT optimization for real-time GPU inference,
#    5) Implement SLAM for GPS-denied environments (defence use case).
