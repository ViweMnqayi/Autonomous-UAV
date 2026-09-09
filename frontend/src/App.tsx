import { useEffect, useMemo, useRef, useState } from "react";
import {
  Plane,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Home,
  Power,
  Navigation,
  Gauge,
  Battery,
  Mountain,
  AlertTriangle,
  Map,
  Compass,
  Activity,
  Shield,
  Target,
  Maximize2,
  Minimize2,
  Satellite,
  Radio,
  Route,
  Crosshair,
  Play,
  Pause,
  RotateCcw,
  Square,
  BrainCircuit,
  Cpu,
  Clock3,
  ChevronRight,
  Zap,
  Circle,
  Server,
  Plus,
  Trash2,
  ZoomIn,
  ZoomOut,
  Wind,
  Thermometer,
  Camera,
  Signal,
  AlertOctagon,
  Video,
  Download,
  List,
  PlayCircle,
  StopCircle,
} from "lucide-react";
import "./index.css";

// ============================================================
// TYPES
// ============================================================

interface DroneStatus {
  state: string;
  position: { x: number; y: number; z: number };
  velocity: { x: number; y: number; z: number };
  speed: { horizontal: number; total: number };
  acceleration: { x: number; y: number; z: number };
  battery: number;
  battery_temperature?: number;
  battery_health?: number;
  flight_time: number;
  distance_travelled: number;
  distance_from_home: number;
  altitude: {
    current: number;
    ground_level: number;
    maximum: number;
    percentage: number;
    warning: string;
  };
  limits: {
    ground_level: number;
    max_altitude: number;
    max_speed: number;
    max_vertical_speed: number;
  };
  home_position: { x: number; y: number; z: number };
  targets: {
    altitude: number;
    speed: number;
    velocity_x: number;
    velocity_y: number;
  };
  navigation: {
    mode: string;
    target_x: number | null;
    target_y: number | null;
  };
  geofence: {
    radius: number;
    distance_from_center: number;
    is_breached: boolean;
    is_warning: boolean;
    distance_percentage: number;
  };
  mission: {
    status: string;
    current_waypoint_index: number;
    total_waypoints: number;
    progress: number;
    current_waypoint: { x: number; y: number; altitude: number } | null;
  };
  wind?: {
    speed_x: number;
    speed_y: number;
    description: string;
  };
  tilt?: {
    roll: number;
    pitch: number;
  };
  terrain?: {
    ground_height: number;
    has_obstacle: boolean;
    in_no_fly_zone: boolean;
  };
  signal?: {
    strength: number;
    quality: string;
    latency: number;
    distance: number;
    signal_lost: boolean;
  };
  emergency?: {
    active: boolean;
    type: string | null;
  };
  recording?: boolean;
}

interface Waypoint {
  id: number;
  x: number;
  y: number;
  altitude: number;
  status: "pending" | "active" | "completed";
}

interface TelemetryPoint {
  time: number;
  altitude: number;
  speed: number;
  battery: number;
  verticalSpeed: number;
}

interface EventItem {
  id: string;
  time: string;
  type: "SYSTEM" | "UAV" | "NAV" | "WARN" | "MISSION" | "AI" | "EMERGENCY";
  message: string;
}

interface Recording {
  name: string;
  size: number;
  size_kb: number;
}

// ============================================================
// CONSTANTS & UTILITIES
// ============================================================

const API = "http://127.0.0.1:8000";
let eventIdCounter = 0;

function generateEventId(): string {
  eventIdCounter++;
  return `event-${Date.now()}-${eventIdCounter}-${Math.random().toString(36).substr(2, 6)}`;
}

function getTime() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatFlightTime(seconds: number) {
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  const remaining = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`;
}

// ============================================================
// APP
// ============================================================

function App() {
  const [drone, setDrone] = useState<DroneStatus | null>(null);
  const [commandStatus, setCommandStatus] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showTelemetryOverlay, setShowTelemetryOverlay] = useState(true);

  const [flightMode, setFlightMode] = useState<"MANUAL" | "AUTONOMOUS">("MANUAL");

  const [missionRunning, setMissionRunning] = useState(false);
  const [missionPaused, setMissionPaused] = useState(false);
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);
  const [currentWaypoint, setCurrentWaypoint] = useState(0);
  const [isSelectingWaypoint, setIsSelectingWaypoint] = useState(false);
  const [selectedAltitude, setSelectedAltitude] = useState(15);

  // Map zoom and pan state
  const [mapZoom, setMapZoom] = useState(1);
  const [mapPanX, setMapPanX] = useState(0);
  const [mapPanY, setMapPanY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Mini-map zoom
  const [miniMapZoom, setMiniMapZoom] = useState(1);

  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryPoint[]>([]);

  const [events, setEvents] = useState<EventItem[]>([
    { id: generateEventId(), time: getTime(), type: "SYSTEM", message: "Ground Control Station initialized" },
  ]);

  const [simulationPaused, setSimulationPaused] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(1);

  // FPV Camera
  const [showFPV, setShowFPV] = useState(false);
  const [fpvFullscreen, setFpvFullscreen] = useState(false);
  const [fpvRecording, setFpvRecording] = useState(false);
  const [fpvZoom, setFpvZoom] = useState(1);

  // Mission Recording
  const [isRecording, setIsRecording] = useState(false);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackProgress, setPlaybackProgress] = useState(0);
  const [showRecordings, setShowRecordings] = useState(false);

  const previousState = useRef<string | null>(null);
  const previousWaypoint = useRef<number>(0);
  const mapRef = useRef<HTMLDivElement>(null);
  const miniMapRef = useRef<HTMLDivElement>(null);
  const fpvCanvasRef = useRef<HTMLCanvasElement>(null);
  const wheelHandlerRef = useRef<((e: WheelEvent) => void) | null>(null);

  // ============================================================
  // HELPERS
  // ============================================================

  const addEvent = (type: EventItem["type"], message: string) => {
    setEvents((current) =>
      [
        { id: generateEventId(), time: getTime(), type, message },
        ...current,
      ].slice(0, 30)
    );
  };

  const sendCommand = async (endpoint: string, method: "POST" = "POST", body?: object) => {
    try {
      const response = await fetch(`${API}${endpoint}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });

      const data = await response.json();

      if (!response.ok) {
        const message = data.detail || data.message || "Command rejected";
        setCommandStatus(message);
        addEvent("WARN", message);
        return;
      }

      setCommandStatus(data.message || "Command accepted");
      fetchTelemetry();
    } catch (error) {
      console.error(error);
      setCommandStatus("Unable to reach backend");
      addEvent("WARN", "Unable to reach UAV backend");
    }
  };

  const fetchTelemetry = async () => {
    try {
      const response = await fetch(`${API}/api/drone/status`);
      if (!response.ok) throw new Error("Failed to retrieve telemetry");

      const data: DroneStatus = await response.json();
      setDrone(data);
      setCommandStatus("");

      if (previousState.current !== null && previousState.current !== data.state) {
        addEvent("UAV", `Flight state changed to ${data.state}`);
      }
      previousState.current = data.state;

      // Check for emergencies
      if (data.emergency?.active) {
        addEvent("EMERGENCY", `⚠️ ${data.emergency.type} detected!`);
      }

      // Update waypoint status from mission
      if (data.mission && data.mission.current_waypoint_index !== undefined) {
        const missionWaypointIndex = data.mission.current_waypoint_index;
        if (missionWaypointIndex !== previousWaypoint.current) {
          previousWaypoint.current = missionWaypointIndex;
          
          setWaypoints((items) =>
            items.map((item, index) => {
              if (index < missionWaypointIndex) {
                return { ...item, status: "completed" };
              } else if (index === missionWaypointIndex) {
                return { ...item, status: "active" };
              } else {
                return { ...item, status: "pending" };
              }
            })
          );
        }
      }

      // Check if mission completed
      if (data.mission && data.mission.status === "COMPLETED" && missionRunning) {
        setMissionRunning(false);
        setMissionPaused(false);
        addEvent("MISSION", "Mission completed! Returning home...");
        setCommandStatus("Mission completed! Returning home");
        
        setWaypoints((items) =>
          items.map((item) => ({ ...item, status: "completed" }))
        );
      }

      setTelemetryHistory((history) => {
        const point: TelemetryPoint = {
          time: Date.now(),
          altitude: data.position.z,
          speed: data.speed.horizontal,
          battery: data.battery,
          verticalSpeed: data.velocity.z,
        };
        return [...history, point].slice(-80);
      });
    } catch (error) {
      console.error(error);
      setCommandStatus("Backend disconnected");
    }
  };

  // ============================================================
  // MAP CONTROLS
  // ============================================================

  const handleZoomIn = () => {
    setMapZoom(prev => Math.min(prev * 1.3, 5));
  };

  const handleZoomOut = () => {
    setMapZoom(prev => Math.max(prev / 1.3, 0.3));
  };

  const handleResetView = () => {
    setMapZoom(1);
    setMapPanX(0);
    setMapPanY(0);
  };

  const handleMiniMapZoomIn = () => {
    setMiniMapZoom(prev => Math.min(prev * 1.3, 3));
  };

  const handleMiniMapZoomOut = () => {
    setMiniMapZoom(prev => Math.max(prev / 1.3, 0.5));
  };

  const handleMapMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isSelectingWaypoint) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMapMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;
      setMapPanX(prev => prev + dx);
      setMapPanY(prev => prev + dy);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMapMouseUp = () => {
    setIsDragging(false);
  };

  // Wheel event handler with passive: false
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setMapZoom(prev => Math.min(Math.max(prev * delta, 0.3), 5));
    };

    wheelHandlerRef.current = handleWheel;

    const element = mapRef.current;
    if (element) {
      element.addEventListener('wheel', handleWheel, { passive: false });
    }

    return () => {
      if (element && wheelHandlerRef.current) {
        element.removeEventListener('wheel', wheelHandlerRef.current);
      }
    };
  }, []);

  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isSelectingWaypoint || !mapRef.current || isDragging) return;

    const rect = mapRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100 - 50;
    const y = -(((e.clientY - rect.top) / rect.height) * 100 - 50);

    const zoomedX = x / mapZoom;
    const zoomedY = y / mapZoom;

    const finalX = zoomedX - (mapPanX / (rect.width / 2));
    const finalY = zoomedY + (mapPanY / (rect.height / 2));

    const clampedX = Math.max(-50, Math.min(50, finalX));
    const clampedY = Math.max(-50, Math.min(50, finalY));

    const newWaypoint: Waypoint = {
      id: waypoints.length + 1,
      x: Math.round(clampedX * 10) / 10,
      y: Math.round(clampedY * 10) / 10,
      altitude: selectedAltitude,
      status: "pending",
    };

    setWaypoints([...waypoints, newWaypoint]);
    addEvent("MISSION", `Waypoint WP${String(newWaypoint.id).padStart(2, "0")} added at (${newWaypoint.x}, ${newWaypoint.y})`);
  };

  // ============================================================
  // EFFECTS
  // ============================================================

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(() => {
      if (!simulationPaused) fetchTelemetry();
    }, 250);
    return () => clearInterval(interval);
  }, [simulationPaused]);

  useEffect(() => {
    const handleKeyboard = (event: KeyboardEvent) => {
      if (!drone || flightMode !== "MANUAL") return;
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;

      switch (event.key.toLowerCase()) {
        case "w":
        case "arrowup":
          sendCommand("/api/drone/move", "POST", { direction: "forward" });
          break;
        case "s":
        case "arrowdown":
          sendCommand("/api/drone/move", "POST", { direction: "backward" });
          break;
        case "a":
        case "arrowleft":
          sendCommand("/api/drone/move", "POST", { direction: "left" });
          break;
        case "d":
        case "arrowright":
          sendCommand("/api/drone/move", "POST", { direction: "right" });
          break;
        case " ":
          event.preventDefault();
          sendCommand("/api/drone/stop");
          break;
        case "f":
          setShowFPV(!showFPV);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyboard);
    return () => window.removeEventListener("keydown", handleKeyboard);
  }, [drone, flightMode]);

  // Load recordings on mount
  useEffect(() => {
    listRecordings();
  }, []);

  // ============================================================
  // FPV Camera Render Loop
  // ============================================================

  useEffect(() => {
    if (!showFPV || !fpvCanvasRef.current || !drone) return;

    const canvas = fpvCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const renderFPV = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Sky gradient
      const gradient = ctx.createLinearGradient(0, 0, 0, height * 0.6);
      gradient.addColorStop(0, '#416f8e');
      gradient.addColorStop(0.5, '#75a6bd');
      gradient.addColorStop(1, '#b7d0d6');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height * 0.6);

      // Ground with terrain
      const groundY = height * 0.6 + (drone.position.z / 50) * height * 0.2;
      const groundGradient = ctx.createLinearGradient(0, groundY, 0, height);
      groundGradient.addColorStop(0, '#7e8b67');
      groundGradient.addColorStop(1, '#5a684f');
      ctx.fillStyle = groundGradient;
      ctx.fillRect(0, groundY, width, height - groundY);

      // Draw obstacles if any
      if (drone.terrain?.has_obstacle) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.fillRect(width * 0.3, groundY - 30, 20, 30);
        ctx.fillRect(width * 0.6, groundY - 50, 25, 50);
      }

      // Grid
      ctx.strokeStyle = 'rgba(255,255,255,0.1)';
      ctx.lineWidth = 1;
      const gridSize = 40 * fpvZoom;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, groundY);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = groundY; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Horizon line with tilt
      ctx.strokeStyle = 'rgba(255,255,255,0.5)';
      ctx.lineWidth = 2;
      const horizonOffset = (drone.tilt?.pitch || 0) * 0.5;
      ctx.beginPath();
      ctx.moveTo(0, groundY + horizonOffset);
      ctx.lineTo(width, groundY + horizonOffset);
      ctx.stroke();

      // HUD
      drawFPVHUD(ctx, width, height, drone);

      // Crosshair
      drawFPVCrosshair(ctx, width, height, drone);

      // Signal and battery indicators
      drawFPVIndicators(ctx, width, height, drone);

      animationId = requestAnimationFrame(renderFPV);
    };

    renderFPV();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [drone, showFPV, fpvZoom]);

  const drawFPVHUD = (ctx: CanvasRenderingContext2D, width: number, height: number, drone: DroneStatus) => {
    const margin = 20;
    ctx.font = '12px monospace';

    // Altitude
    ctx.fillStyle = '#00ff88';
    ctx.textAlign = 'left';
    ctx.fillText(`ALT ${drone.position.z.toFixed(1)}m`, margin, margin + 15);

    // Speed
    ctx.fillStyle = '#00aaff';
    ctx.fillText(`SPD ${drone.speed.horizontal.toFixed(1)}m/s`, margin, margin + 35);

    // Heading
    ctx.fillStyle = '#ffaa00';
    const heading = Math.atan2(drone.velocity.y, drone.velocity.x) * 180 / Math.PI;
    ctx.fillText(`HDG ${heading.toFixed(0)}°`, margin, margin + 55);

    // Distance
    ctx.fillStyle = '#ff88ff';
    ctx.fillText(`DIST ${drone.distance_from_home.toFixed(1)}m`, margin, margin + 75);

    // Battery
    const batteryColor = drone.battery > 50 ? '#00ff88' : drone.battery > 20 ? '#ffaa00' : '#ff4444';
    ctx.fillStyle = batteryColor;
    ctx.fillText(`BAT ${drone.battery.toFixed(0)}%`, margin, margin + 95);

    // Signal quality
    const signalStrength = drone.signal?.strength || 0;
    const signalColor = signalStrength > 0.6 ? '#00ff88' : signalStrength > 0.3 ? '#ffaa00' : '#ff4444';
    ctx.fillStyle = signalColor;
    ctx.fillText(`SIG ${drone.signal?.quality || 'Unknown'}`, margin, margin + 115);

    // Emergency warning
    if (drone.emergency?.active) {
      ctx.fillStyle = '#ff0000';
      ctx.font = 'bold 16px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('⚠️ EMERGENCY', width / 2, 30);
    }

    // Recording indicator
    if (fpvRecording) {
      ctx.fillStyle = '#ff0000';
      ctx.textAlign = 'right';
      ctx.font = 'bold 14px monospace';
      ctx.fillText('● REC', width - margin, margin + 15);
    }
  };

  const drawFPVCrosshair = (ctx: CanvasRenderingContext2D, width: number, height: number, drone: DroneStatus) => {
    const cx = width / 2;
    const cy = height / 2;
    const size = 20;

    ctx.strokeStyle = 'rgba(0,255,0,0.5)';
    ctx.lineWidth = 1;

    // Outer circle
    ctx.beginPath();
    ctx.arc(cx, cy, size, 0, Math.PI * 2);
    ctx.stroke();

    // Cross hairs
    ctx.beginPath();
    ctx.moveTo(cx - size * 0.7, cy);
    ctx.lineTo(cx - size * 0.3, cy);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx + size * 0.3, cy);
    ctx.lineTo(cx + size * 0.7, cy);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx, cy - size * 0.7);
    ctx.lineTo(cx, cy - size * 0.3);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx, cy + size * 0.3);
    ctx.lineTo(cx, cy + size * 0.7);
    ctx.stroke();

    // Center dot
    ctx.fillStyle = 'rgba(0,255,0,0.8)';
    ctx.beginPath();
    ctx.arc(cx, cy, 2, 0, Math.PI * 2);
    ctx.fill();

    // Tilt indicators - only roll is used for crosshair
    const tiltRoll = drone.tilt?.roll || 0;
    
    ctx.strokeStyle = 'rgba(0,255,255,0.3)';
    ctx.lineWidth = 1;
    // Roll indicator
    ctx.beginPath();
    ctx.arc(cx, cy, size * 1.5, 0, Math.PI * 2);
    ctx.stroke();
    
    // Roll line
    ctx.beginPath();
    ctx.moveTo(cx - size * 1.2, cy + Math.sin(tiltRoll * Math.PI / 180) * size * 0.8);
    ctx.lineTo(cx + size * 1.2, cy - Math.sin(tiltRoll * Math.PI / 180) * size * 0.8);
    ctx.stroke();
  };

  const drawFPVIndicators = (ctx: CanvasRenderingContext2D, width: number, height: number, drone: DroneStatus) => {
    const margin = 20;
    const x = width - margin;
    const y = margin;

    // Signal bars
    const signalBars = 4;
    const barWidth = 6;
    const barSpacing = 4;
    const barHeight = 16;
    const signalStrength = drone.signal?.strength || 1;

    for (let i = 0; i < signalBars; i++) {
      const barX = x - (signalBars - i) * (barWidth + barSpacing);
      const barHeightFilled = (i + 1) / signalBars * barHeight;
      const isActive = signalStrength > (i / signalBars);

      ctx.fillStyle = isActive ? (signalStrength > 0.6 ? '#00ff88' : signalStrength > 0.3 ? '#ffaa00' : '#ff4444') : 'rgba(255,255,255,0.2)';
      ctx.fillRect(barX, y + barHeight - barHeightFilled, barWidth, barHeightFilled);
    }

    // GPS lock indicator
    ctx.fillStyle = '#00ff88';
    ctx.font = '10px monospace';
    ctx.textAlign = 'right';
    ctx.fillText('GPS LOCK', x, y + barHeight + 20);
  };

  // ============================================================
  // RECORDING FUNCTIONS
  // ============================================================

  const startRecording = async () => {
    try {
      const response = await fetch(`${API}/api/replay/start`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setIsRecording(true);
        addEvent("SYSTEM", "Mission recording started");
        setCommandStatus("Recording started");
      }
    } catch (error) {
      console.error(error);
      addEvent("WARN", "Failed to start recording");
    }
  };

  const stopRecording = async () => {
    try {
      const response = await fetch(`${API}/api/replay/stop`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setIsRecording(false);
        addEvent("SYSTEM", `Mission recording saved (${data.frames} frames)`);
        setCommandStatus(`Recording saved: ${data.filename}`);
        await listRecordings();
      }
    } catch (error) {
      console.error(error);
      addEvent("WARN", "Failed to stop recording");
    }
  };

  const listRecordings = async () => {
    try {
      const response = await fetch(`${API}/api/replay/list`);
      const data = await response.json();
      setRecordings(data.recordings || []);
    } catch (error) {
      console.error(error);
    }
  };

  const loadRecording = async (filename: string) => {
    try {
      const response = await fetch(`${API}/api/replay/load?filename=${filename}`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        addEvent("SYSTEM", `Loaded recording: ${filename}`);
        setCommandStatus(`Loaded ${filename} (${data.frames} frames)`);
        await startPlayback();
      }
    } catch (error) {
      console.error(error);
      addEvent("WARN", "Failed to load recording");
    }
  };

  const startPlayback = async () => {
    try {
      const response = await fetch(`${API}/api/replay/play`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setIsPlaying(true);
        addEvent("SYSTEM", "Playback started");
        setCommandStatus("Playback started");
        // Start polling for playback frames
        pollPlayback();
      }
    } catch (error) {
      console.error(error);
      addEvent("WARN", "Failed to start playback");
    }
  };

  const stopPlayback = async () => {
    try {
      await fetch(`${API}/api/replay/stop`, { method: 'POST' });
      setIsPlaying(false);
      setPlaybackProgress(0);
      addEvent("SYSTEM", "Playback stopped");
      setCommandStatus("Playback stopped");
    } catch (error) {
      console.error(error);
    }
  };

  const pollPlayback = async () => {
    if (!isPlaying) return;

    try {
      const response = await fetch(`${API}/api/replay/frame`);
      const data = await response.json();
      
      if (data.playing) {
        if (data.frame) {
          // Update drone position with playback data
          setDrone(prev => {
            if (!prev) return prev;
            const frame = data.frame;
            return {
              ...prev,
              position: frame.position || prev.position,
              velocity: frame.velocity || prev.velocity,
              speed: frame.speed || prev.speed,
              battery: frame.battery || prev.battery,
              state: frame.state || prev.state,
              altitude: frame.altitude || prev.altitude,
            };
          });
        }
        setPlaybackProgress(data.progress || 0);
        
        // Continue polling
        setTimeout(pollPlayback, 100);
      } else if (data.complete) {
        setIsPlaying(false);
        setPlaybackProgress(1);
        addEvent("SYSTEM", "Playback complete");
        setCommandStatus("Playback complete");
      }
    } catch (error) {
      console.error(error);
    }
  };

  // ============================================================
  // EMERGENCY FUNCTIONS
  // ============================================================

  const triggerEmergency = async (type: string) => {
    try {
      const response = await fetch(`${API}/api/emergency/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      });
      const data = await response.json();
      if (data.success) {
        addEvent("EMERGENCY", `⚠️ ${type.toUpperCase()} triggered: ${data.message}`);
        setCommandStatus(`Emergency: ${type}`);
      }
    } catch (error) {
      console.error(error);
      addEvent("WARN", "Failed to trigger emergency");
    }
  };

  const resolveEmergency = async () => {
    try {
      const response = await fetch(`${API}/api/emergency/resolve`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        addEvent("SYSTEM", "Emergency resolved");
        setCommandStatus("Emergency resolved");
      }
    } catch (error) {
      console.error(error);
    }
  };

  // ============================================================
  // WAYPOINT HANDLERS
  // ============================================================

  const removeWaypoint = (id: number) => {
    setWaypoints(waypoints.filter(w => w.id !== id));
    addEvent("MISSION", `Waypoint WP${String(id).padStart(2, "0")} removed`);
  };

  const clearWaypoints = () => {
    setWaypoints([]);
    addEvent("MISSION", "All waypoints cleared");
  };

  const updateWaypointAltitude = (id: number, altitude: number) => {
    setWaypoints(waypoints.map(w =>
      w.id === id ? { ...w, altitude: Math.max(0, Math.min(120, altitude)) } : w
    ));
  };

  // ============================================================
  // MISSION HANDLERS
  // ============================================================

  const startMission = async () => {
    if (!drone) return;

    if (drone.state !== "FLYING") {
      setCommandStatus("Drone must be flying to start mission");
      addEvent("WARN", "Mission start rejected: UAV is not flying");
      return;
    }

    if (waypoints.length === 0) {
      setCommandStatus("No waypoints set. Add waypoints first.");
      addEvent("WARN", "Mission start rejected: No waypoints");
      return;
    }

    const waypointsData = waypoints.map(w => ({
      x: w.x,
      y: w.y,
      altitude: w.altitude
    }));

    try {
      const loadResponse = await fetch(`${API}/api/mission/load`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ waypoints: waypointsData })
      });

      if (!loadResponse.ok) {
        throw new Error("Failed to load mission");
      }

      const startResponse = await fetch(`${API}/api/mission/start`, {
        method: "POST"
      });

      if (!startResponse.ok) {
        throw new Error("Failed to start mission");
      }

      const data = await startResponse.json();
      setMissionRunning(true);
      setMissionPaused(false);
      setCurrentWaypoint(0);

      setWaypoints((items) =>
        items.map((item, index) => ({
          ...item,
          status: index === 0 ? "active" : "pending",
        }))
      );

      addEvent("MISSION", "Autonomous mission started");
      setCommandStatus("Mission started");
      setFlightMode("AUTONOMOUS");
    } catch (error) {
      console.error(error);
      addEvent("WARN", "Failed to start mission");
      setCommandStatus("Failed to start mission");
    }
  };

  const pauseMission = async () => {
    try {
      await fetch(`${API}/api/mission/pause`, { method: "POST" });
      setMissionPaused(true);
      addEvent("MISSION", "Mission paused");
    } catch (error) {
      console.error(error);
    }
  };

  const resumeMission = async () => {
    try {
      await fetch(`${API}/api/mission/resume`, { method: "POST" });
      setMissionPaused(false);
      addEvent("MISSION", "Mission resumed");
    } catch (error) {
      console.error(error);
    }
  };

  const abortMission = async () => {
    try {
      await fetch(`${API}/api/mission/abort`, { method: "POST" });
      setMissionRunning(false);
      setMissionPaused(false);
      setWaypoints((items) => items.map((item) => ({ ...item, status: "pending" })));
      setCurrentWaypoint(0);
      addEvent("MISSION", "Mission aborted");
      setCommandStatus("Mission aborted");
    } catch (error) {
      console.error(error);
    }
  };

  const resetMission = async () => {
    try {
      await fetch(`${API}/api/mission/reset`, { method: "POST" });
      setMissionRunning(false);
      setMissionPaused(false);
      setCurrentWaypoint(0);
      setWaypoints([]);
      addEvent("MISSION", "Mission reset");
      setCommandStatus("Mission reset");
    } catch (error) {
      console.error(error);
    }
  };

  // ============================================================
  // FLIGHT HANDLERS
  // ============================================================

  const handleTakeoff = () => {
    addEvent("UAV", "Takeoff command issued");
    sendCommand("/api/drone/takeoff");
  };

  const handleLand = () => {
    addEvent("UAV", "Landing command issued");
    sendCommand("/api/drone/land");
  };

  const handleRTH = () => {
    addEvent("NAV", "Return-to-home command issued");
    sendCommand("/api/drone/return-home");
  };

  const handleEmergency = () => {
    addEvent("WARN", "Emergency stop activated");
    sendCommand("/api/drone/emergency-stop");
    setMissionRunning(false);
    setMissionPaused(false);
  };

  const handleFlightModeChange = async (mode: "MANUAL" | "AUTONOMOUS") => {
    setFlightMode(mode);
    addEvent("NAV", `Flight mode changed to ${mode}`);

    if (mode === "AUTONOMOUS") {
      if (waypoints.length > 0) {
        await startMission();
      } else {
        setCommandStatus("Add waypoints before switching to autonomous mode");
      }
    } else {
      if (missionRunning) {
        await abortMission();
      }
    }
  };

  const handleSimulationSpeedChange = async (speed: number) => {
    setSimulationSpeed(speed);
    try {
      await fetch(`${API}/api/simulation/speed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed })
      });
      addEvent("SYSTEM", `Simulation speed set to ${speed}x`);
    } catch (error) {
      console.error(error);
    }
  };

  const handleSetGeofence = async (radius: number) => {
    try {
      await fetch(`${API}/api/geofence/set`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ radius })
      });
      addEvent("SYSTEM", `Geofence radius set to ${radius}m`);
    } catch (error) {
      console.error(error);
    }
  };

  const handleSetWind = async (speed: number) => {
    try {
      await fetch(`${API}/api/drone/wind`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed })
      });
      addEvent("SYSTEM", `Wind speed set to ${speed} m/s`);
    } catch (error) {
      console.error(error);
    }
  };

  // ============================================================
  // COMPUTED VALUES
  // ============================================================

  const missionProgress = useMemo(() => {
    if (waypoints.length === 0) return 0;
    const completed = waypoints.filter((w) => w.status === "completed").length;
    return (completed / waypoints.length) * 100;
  }, [waypoints]);

  if (!drone) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner">
          <Plane size={48} className="loading-plane" />
        </div>
        <h2>Initializing UAV Systems</h2>
        <p>Establishing telemetry link...</p>
        <div className="loading-progress">
          <div className="loading-bar" />
        </div>
      </div>
    );
  }

  // Map zoom and pan calculations
  const worldScale = 4 * mapZoom;
  const worldX = -drone.position.x * worldScale + mapPanX;
  const worldY = drone.position.y * worldScale + mapPanY;
  const altitudePercentage = drone.altitude.percentage;
  const groundScale = (1.5 - (altitudePercentage / 100) * 0.75) * mapZoom;
  const groundVerticalPosition = 55 + altitudePercentage * 0.22;

  const isLowAltitude = drone.altitude.warning === "LOW_ALTITUDE";
  const isHighAltitude = drone.altitude.warning === "HIGH_ALTITUDE";
  const isGrounded = drone.altitude.warning === "GROUND";

  const batteryColor =
    drone.battery > 50 ? "#4ade80" : drone.battery > 20 ? "#fbbf24" : "#ef4444";

  const isFlying = drone.state === "FLYING";

  const backendConnected =
    commandStatus !== "Backend disconnected" && commandStatus !== "Unable to reach backend";

  const aiAnomalyScore = Math.min(
    0.95,
    (Math.abs(drone.velocity.z) / Math.max(drone.limits.max_vertical_speed, 1)) * 0.35 +
      ((100 - drone.battery) / 100) * 0.15
  );

  const aiRisk = aiAnomalyScore > 0.65 ? "HIGH" : aiAnomalyScore > 0.35 ? "MODERATE" : "LOW";

  const geofenceColor = drone.geofence.is_breached
    ? "#ef4444"
    : drone.geofence.is_warning
    ? "#fbbf24"
    : "#00d084";

  // Wind speed total
  const windTotal = drone.wind ? Math.sqrt(drone.wind.speed_x ** 2 + drone.wind.speed_y ** 2) : 0;
  const windColor = windTotal > 5 ? "#fbbf24" : windTotal > 3 ? "#4a9eff" : "#00d084";

  // Battery health status
  const batteryHealth = drone.battery_health || 100;
  
  // Battery temperature
  const batteryTemp = drone.battery_temperature || 25;

  // Drone tilt for visualization
  const tiltRoll = drone.tilt?.roll || 0;
  const tiltPitch = drone.tilt?.pitch || 0;

  // Signal strength
  const signalStrength = drone.signal?.strength || 1;
  const signalColor = signalStrength > 0.6 ? "#4ade80" : signalStrength > 0.3 ? "#fbbf24" : "#ef4444";

  return (
    <div className={`app ${isFullscreen ? "fullscreen" : ""}`}>
      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Plane size={24} className="brand-plane" />
          </div>
          <div>
            <h1>UAV Command Center</h1>
            <span>Autonomous Ground Control Station v5.0</span>
          </div>
        </div>

        <div className="system-status">
          <MiniHealth icon={<Server size={13} />} label="API" active={backendConnected} />
          <MiniHealth icon={<Satellite size={13} />} label="GPS" active={true} />
          <MiniHealth icon={<Radio size={13} />} label="LINK" active={backendConnected} />
          <MiniHealth icon={<Circle size={13} />} label="GEOFENCE" active={!drone.geofence.is_breached} />
          <MiniHealth icon={<Wind size={13} />} label="WIND" active={windTotal < 5} />
          <MiniHealth icon={<Signal size={13} />} label="SIGNAL" active={signalStrength > 0.3} />
          {drone.emergency?.active && (
            <MiniHealth icon={<AlertOctagon size={13} />} label="EMERGENCY" active={false} />
          )}
        </div>

        <div className="topbar-controls">
          <button
            className="icon-button"
            onClick={() => setShowFPV(!showFPV)}
            title="Toggle FPV Camera (F)"
          >
            <Camera size={18} />
          </button>
          <button
            className="icon-button"
            onClick={() => setShowTelemetryOverlay(!showTelemetryOverlay)}
            title="Toggle telemetry overlay"
          >
            <Activity size={18} />
          </button>
          <button
            className="icon-button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title="Toggle fullscreen"
          >
            {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <div className="connection">
            <span className="connection-dot pulse" />
            <span className="connection-text">SIMULATOR</span>
            <span className="connection-status">ACTIVE</span>
          </div>
        </div>
      </header>

      {/* =====================================================
          DASHBOARD
      ===================================================== */}

      <main className="dashboard">
        {/* ===================================================
            LEFT SIDE
        =================================================== */}

        <section className="main-content">
          {/* FLIGHT VIEW */}

          <section className="flight-panel">
            <div className="panel-header">
              <div className="panel-header-left">
                <h2>Live Flight Environment</h2>
                <span className="panel-subtitle">
                  <Compass size={14} />
                  {isSelectingWaypoint ? (
                    <span style={{ color: "#4a9eff" }}>
                      ✏️ Click map to add waypoint (Zoom: {mapZoom.toFixed(1)}x)
                    </span>
                  ) : (
                    <span>Zoom: {mapZoom.toFixed(1)}x • Drag to pan</span>
                  )}
                  {drone.geofence.is_breached && (
                    <span style={{ color: "#ef4444", marginLeft: "8px" }}>
                      ⚠️ GEOFENCE BREACHED
                    </span>
                  )}
                  {windTotal > 3 && (
                    <span style={{ color: windColor, marginLeft: "8px" }}>
                      🌬️ {drone.wind?.description || "Windy"}
                    </span>
                  )}
                  {drone.terrain?.has_obstacle && (
                    <span style={{ color: "#fbbf24", marginLeft: "8px" }}>
                      ⚠️ OBSTACLE NEARBY
                    </span>
                  )}
                  {drone.terrain?.in_no_fly_zone && (
                    <span style={{ color: "#ef4444", marginLeft: "8px" }}>
                      🚫 NO-FLY ZONE
                    </span>
                  )}
                </span>
              </div>

              <div className="flight-header-right">
                <div className="flight-mode-badge">
                  <span
                    className={
                      flightMode === "AUTONOMOUS"
                        ? "mode-dot autonomous"
                        : "mode-dot manual"
                    }
                  />
                  {flightMode}
                </div>
                <div className="flight-state">
                  <span className={`state-dot ${drone.state.toLowerCase()}`} />
                  <span className="state-text">{drone.state}</span>
                </div>
                {/* Map Controls */}
                <div className="map-controls">
                  <button className="map-control-btn" onClick={handleZoomIn} title="Zoom In">
                    <ZoomIn size={14} />
                  </button>
                  <button className="map-control-btn" onClick={handleZoomOut} title="Zoom Out">
                    <ZoomOut size={14} />
                  </button>
                  <button className="map-control-btn" onClick={handleResetView} title="Reset View">
                    <Home size={14} />
                  </button>
                </div>
              </div>
            </div>

            <div 
              className={`flight-view ${isSelectingWaypoint ? "selecting-waypoint" : ""}`}
              onClick={handleMapClick}
              onMouseDown={handleMapMouseDown}
              onMouseMove={handleMapMouseMove}
              onMouseUp={handleMapMouseUp}
              onMouseLeave={handleMapMouseUp}
              ref={mapRef}
            >
              {/* SKY - Enhanced with more clouds */}
              <div className="sky">
                <div className="sky-gradient" />
                <div className="sun" />
                <div className="cloud cloud-one" />
                <div className="cloud cloud-two" />
                <div className="cloud cloud-three" />
                <div className="cloud cloud-four" />
                <div className="cloud cloud-five" />
                <div className="cloud cloud-six" />
              </div>

              {/* HORIZON */}
              <div
                className="horizon"
                style={{ transform: `translateY(${altitudePercentage * 0.15}px)` }}
              />

              {/* WORLD */}
              <div
                className="world"
                style={{
                  transform: `
                    translate3d(${worldX}px, ${worldY}px, 0)
                    scale(${groundScale})
                  `,
                  top: `${groundVerticalPosition}%`,
                  transition: isDragging ? 'none' : 'transform 150ms ease, top 150ms ease',
                }}
              >
                <div className="ground">
                  <div className="ground-grid" />

                  {/* GEOFENCE */}
                  <div
                    className="geofence"
                    style={{
                      borderColor: geofenceColor,
                      boxShadow: `0 0 35px ${geofenceColor}22`,
                    }}
                  >
                    <span>GEOFENCE {drone.geofence.radius}m</span>
                  </div>

                  {/* HOME */}
                  <div
                    className="home-marker"
                    style={{
                      left: `${50 + drone.home_position.x * worldScale / mapZoom}%`,
                      top: `${50 - drone.home_position.y * worldScale / mapZoom}%`,
                    }}
                  >
                    <div className="home-marker-icon">
                      <Home size={18} />
                    </div>
                    <span>HOME</span>
                  </div>

                  {/* WAYPOINTS */}
                  {waypoints.map((waypoint) => (
                    <div
                      key={waypoint.id}
                      className={`map-waypoint ${waypoint.status}`}
                      style={{
                        left: `${50 + waypoint.x * (worldScale / mapZoom)}%`,
                        top: `${50 - waypoint.y * (worldScale / mapZoom)}%`,
                      }}
                    >
                      <span>WP{String(waypoint.id).padStart(2, "0")}</span>
                      {waypoint.status === "active" && (
                        <div className="waypoint-active-indicator" />
                      )}
                    </div>
                  ))}

                  {/* WORLD MARKERS */}
                  <div className="world-marker marker-one">
                    <span>🏛️ ZONE A</span>
                  </div>
                  <div className="world-marker marker-two">
                    <span>🌲 ZONE B</span>
                  </div>
                  <div className="world-marker marker-three">
                    <span>📍 SURVEY AREA</span>
                  </div>

                  <div className="ground-radar" />
                </div>
              </div>

              {/* WIND INDICATOR */}
              <div className="wind-indicator">
                <Wind size={16} className="wind-icon" style={{ color: windColor }} />
                <span className="wind-speed">
                  {drone.wind?.description || "Calm"} ({windTotal.toFixed(1)} m/s)
                </span>
                <div 
                  className="wind-arrow"
                  style={{ 
                    transform: `rotate(${Math.atan2(drone.wind?.speed_y || 0, drone.wind?.speed_x || 0) * 180 / Math.PI}deg)`,
                    color: windColor
                  }}
                >
                  ↑
                </div>
              </div>

              {/* SIGNAL INDICATOR */}
              <div className="signal-indicator">
                <Signal size={16} style={{ color: signalColor }} />
                <span className="signal-quality" style={{ color: signalColor }}>
                  {drone.signal?.quality || "Unknown"}
                </span>
                <span className="signal-strength">
                  {((drone.signal?.strength || 1) * 100).toFixed(0)}%
                </span>
              </div>

              {/* FLIGHT TRAJECTORY */}
              <Trajectory history={telemetryHistory} drone={drone} />

              {/* CAMERA CROSSHAIR */}
              <div className="camera-center">
                <div className="crosshair horizontal" />
                <div className="crosshair vertical" />
                <div className="crosshair-dot" />
              </div>

              {/* DRONE - With Tilt Animation */}
              <div className="drone-camera">
                <div 
                  className={`drone-model ${drone.state === "FLYING" ? "flying" : ""}`}
                  style={{
                    transform: `
                      rotateX(${tiltPitch}deg) 
                      rotateZ(${tiltRoll}deg)
                    `
                  }}
                >
                  <Plane size={44} className="drone-icon" />
                  <div className="drone-glow" />
                </div>
                <div className="drone-shadow" />
              </div>

              {/* DRONE TILT INDICATOR */}
              <div className="drone-tilt-indicator">
                <span>TILT</span>
                <div className="tilt-values">
                  <span>
                    <span className="tilt-roll">⟳</span>
                    <strong>{tiltRoll.toFixed(1)}°</strong>
                  </span>
                  <span>
                    <span className="tilt-pitch">⟳</span>
                    <strong>{tiltPitch.toFixed(1)}°</strong>
                  </span>
                </div>
              </div>

              {/* WARNINGS */}
              {isLowAltitude && (
                <div className="flight-warning warning-low">
                  <AlertTriangle size={16} />
                  LOW ALTITUDE
                </div>
              )}
              {isHighAltitude && (
                <div className="flight-warning warning-high">
                  <AlertTriangle size={16} />
                  HIGH ALTITUDE
                </div>
              )}
              {drone.battery <= 20 && (
                <div className="flight-warning warning-battery">
                  <Battery size={16} />
                  LOW BATTERY
                </div>
              )}
              {drone.geofence.is_breached && (
                <div className="flight-warning warning-high">
                  <AlertTriangle size={16} />
                  GEOFENCE BREACHED
                </div>
              )}
              {drone.emergency?.active && (
                <div className="flight-warning warning-high" style={{ background: 'rgba(180, 60, 60, 0.95)' }}>
                  <AlertOctagon size={16} />
                  {drone.emergency.type?.toUpperCase() || 'EMERGENCY'}
                </div>
              )}
              {drone.signal?.signal_lost && (
                <div className="flight-warning warning-high">
                  <Signal size={16} />
                  SIGNAL LOST
                </div>
              )}
              {isGrounded && (
                <div className="ground-status">
                  <Navigation size={16} />
                  GROUNDED
                </div>
              )}
              {windTotal > 5 && (
                <div className="flight-warning warning-low">
                  <Wind size={16} />
                  HIGH WIND
                </div>
              )}
              {drone.terrain?.has_obstacle && (
                <div className="flight-warning warning-low">
                  <AlertTriangle size={16} />
                  OBSTACLE NEARBY
                </div>
              )}
              {drone.terrain?.in_no_fly_zone && (
                <div className="flight-warning warning-high">
                  <AlertTriangle size={16} />
                  NO-FLY ZONE
                </div>
              )}

              {/* TELEMETRY OVERLAY */}
              {showTelemetryOverlay && (
                <div className="flight-overlay">
                  <OverlayMetric
                    label="ALTITUDE"
                    value={drone.position.z.toFixed(1)}
                    unit="m"
                  />
                  <OverlayMetric
                    label="SPEED"
                    value={drone.speed.horizontal.toFixed(1)}
                    unit="m/s"
                  />
                  <OverlayMetric
                    label="BATTERY"
                    value={drone.battery.toFixed(0)}
                    unit="%"
                    valueColor={batteryColor}
                  />
                  <OverlayMetric
                    label="FLIGHT"
                    value={formatFlightTime(drone.flight_time)}
                  />
                  <OverlayMetric
                    label="MISSION"
                    value={`${drone.mission.progress.toFixed(0)}%`}
                  />
                  <OverlayMetric
                    label="WP"
                    value={`${Math.min(drone.mission.current_waypoint_index + 1, drone.mission.total_waypoints)}/${drone.mission.total_waypoints || waypoints.length}`}
                  />
                  <OverlayMetric
                    label="SIGNAL"
                    value={((drone.signal?.strength || 1) * 100).toFixed(0)}
                    unit="%"
                    valueColor={signalColor}
                  />
                </div>
              )}

              {/* COORDINATES */}
              <div className="coordinates">
                <span className="coord-item">
                  <span className="coord-label">X</span>
                  <span className="coord-value">{drone.position.x.toFixed(1)}m</span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">Y</span>
                  <span className="coord-value">{drone.position.y.toFixed(1)}m</span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">Z</span>
                  <span className="coord-value">{drone.position.z.toFixed(1)}m</span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">DIST</span>
                  <span className="coord-value">{drone.distance_from_home.toFixed(1)}m</span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">GEOFENCE</span>
                  <span
                    className="coord-value"
                    style={{
                      color: geofenceColor,
                    }}
                  >
                    {drone.geofence.distance_percentage.toFixed(0)}%
                  </span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">WP</span>
                  <span className="coord-value">
                    {waypoints.length > 0 ? `${Math.min(drone.mission.current_waypoint_index + 1, drone.mission.total_waypoints || waypoints.length)}/${waypoints.length}` : "0/0"}
                  </span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">WIND</span>
                  <span className="coord-value" style={{ color: windColor }}>
                    {windTotal.toFixed(1)} m/s
                  </span>
                </span>
                <span className="coord-divider" />
                <span className="coord-item">
                  <span className="coord-label">SIGNAL</span>
                  <span className="coord-value" style={{ color: signalColor }}>
                    {((drone.signal?.strength || 1) * 100).toFixed(0)}%
                  </span>
                </span>
                {drone.terrain && (
                  <>
                    <span className="coord-divider" />
                    <span className="coord-item">
                      <span className="coord-label">TERRAIN</span>
                      <span className="coord-value" style={{ color: drone.terrain.has_obstacle ? "#ef4444" : drone.terrain.in_no_fly_zone ? "#fbbf24" : "#4ade80" }}>
                        {drone.terrain.has_obstacle ? "⚠️" : drone.terrain.in_no_fly_zone ? "🚫" : "✓"}
                      </span>
                    </span>
                  </>
                )}
              </div>
            </div>
          </section>

          {/* LOWER DASHBOARD */}
          <div className="lower-dashboard">
            {/* MAP */}
            <section className="card map-card">
              <div className="card-title">
                <Map size={18} />
                <span>Navigation Map</span>
                <span className="card-title-right">LIVE</span>
                <div className="mini-map-controls">
                  <button className="mini-map-control-btn" onClick={handleMiniMapZoomIn} title="Zoom In">
                    <ZoomIn size={12} />
                  </button>
                  <button className="mini-map-control-btn" onClick={handleMiniMapZoomOut} title="Zoom Out">
                    <ZoomOut size={12} />
                  </button>
                </div>
                {drone.geofence.is_warning && (
                  <span style={{ color: "#fbbf24", fontSize: "8px", marginLeft: "auto" }}>
                    ⚠️ NEAR BOUNDARY
                  </span>
                )}
              </div>

              <div className="navigation-map" ref={miniMapRef}>
                <div className="map-grid" />

                {/* GEOFENCE on map */}
                <div
                  className="map-geofence"
                  style={{
                    borderColor: geofenceColor,
                    width: `${drone.geofence.radius * 0.7 * miniMapZoom}%`,
                    height: `${drone.geofence.radius * 0.7 * miniMapZoom}%`,
                    left: `${50 - (drone.geofence.radius * 0.35 * miniMapZoom)}%`,
                    top: `${50 - (drone.geofence.radius * 0.35 * miniMapZoom)}%`,
                  }}
                />

                <div className="map-home">
                  <Home size={14} />
                </div>

                <div className="map-path">
                  <div className="path-line" />
                </div>

                {waypoints.map((waypoint) => (
                  <div
                    key={waypoint.id}
                    className={`navigation-waypoint ${waypoint.status}`}
                    style={{
                      left: `${50 + waypoint.x * 0.7 * miniMapZoom}%`,
                      top: `${50 - waypoint.y * 0.7 * miniMapZoom}%`,
                    }}
                  >
                    <span>{waypoint.id}</span>
                  </div>
                ))}

                <div
                  className="map-drone"
                  style={{
                    left: `${50 + drone.position.x * 0.7 * miniMapZoom}%`,
                    top: `${50 - drone.position.y * 0.7 * miniMapZoom}%`,
                  }}
                >
                  <Plane size={17} />
                </div>

                <div className="map-label home-label">HOME</div>
                <div className="map-label drone-label">UAV</div>
              </div>
            </section>

            {/* TELEMETRY GRAPH */}
            <section className="card graph-card">
              <div className="card-title">
                <Activity size={18} />
                <span>Flight Telemetry</span>
                <span className="graph-live">
                  <span />
                  LIVE
                </span>
              </div>
              <TelemetryGraph history={telemetryHistory} />
            </section>
          </div>

          {/* SYSTEM / EVENTS */}
          <div className="bottom-dashboard">
            <section className="card health-card">
              <div className="card-title">
                <Shield size={18} />
                <span>System Health</span>
                <span className="health-status">
                  {drone.emergency?.active ? "⚠️ EMERGENCY" : drone.geofence.is_breached ? "⚠️ GEOFENCE BREACHED" : "ALL SYSTEMS NOMINAL"}
                </span>
              </div>

              <div className="health-grid">
                <HealthItem icon={<Cpu size={15} />} label="Flight Controller" value="NORMAL" />
                <HealthItem icon={<Satellite size={15} />} label="GPS" value={drone.signal?.signal_lost ? "LOST" : "LOCKED"} />
                <HealthItem icon={<Activity size={15} />} label="IMU" value="NORMAL" />
                <HealthItem icon={<Radio size={15} />} label="Telemetry" value={drone.signal?.signal_lost ? "LOST" : "CONNECTED"} />
                <HealthItem
                  icon={<Navigation size={15} />}
                  label="Navigation"
                  value={flightMode === "AUTONOMOUS" ? "AUTO" : "MANUAL"}
                />
                <HealthItem
                  icon={<Battery size={15} />}
                  label="Power"
                  value={drone.battery > 20 ? "NORMAL" : "LOW"}
                />
              </div>
            </section>

            <section className="card event-card">
              <div className="card-title">
                <Clock3 size={18} />
                <span>Event Log</span>
              </div>
              <div className="event-list">
                {events.slice(0, 8).map((event) => (
                  <div className="event-item" key={event.id}>
                    <span className={`event-type ${event.type.toLowerCase()}`}>
                      {event.type}
                    </span>
                    <span className="event-time">{event.time}</span>
                    <span className="event-message">{event.message}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </section>

        {/* ===================================================
            RIGHT SIDEBAR
        =================================================== */}

        <aside className="side-panel">
          {/* QUICK STATUS */}
          <div className="status-grid">
            <div className="status-card">
              <div className="status-icon">
                <Gauge size={16} />
              </div>
              <div className="status-content">
                <span className="status-label">Speed</span>
                <span className="status-value">
                  {drone.speed.horizontal.toFixed(1)}
                  <small> m/s</small>
                </span>
              </div>
            </div>

            <div className="status-card">
              <div className="status-icon">
                <Satellite size={16} />
              </div>
              <div className="status-content">
                <span className="status-label">Alt</span>
                <span className="status-value">
                  {drone.position.z.toFixed(1)}
                  <small> m</small>
                </span>
              </div>
            </div>

            <div className="status-card">
              <div className="status-icon">
                <Battery size={16} />
              </div>
              <div className="status-content">
                <span className="status-label">Battery</span>
                <span className="status-value" style={{ color: batteryColor }}>
                  {drone.battery.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* FLIGHT MODE */}
          <section className="card mode-card">
            <div className="card-title">
              <Navigation size={18} />
              <span>Flight Mode</span>
            </div>

            <div className="mode-selector">
              <button
                className={flightMode === "MANUAL" ? "mode-button active" : "mode-button"}
                onClick={() => handleFlightModeChange("MANUAL")}
              >
                <Crosshair size={16} />
                <div>
                  <strong>MANUAL</strong>
                  <small>Pilot control</small>
                </div>
              </button>

              <button
                className={
                  flightMode === "AUTONOMOUS"
                    ? "mode-button active autonomous"
                    : "mode-button"
                }
                onClick={() => handleFlightModeChange("AUTONOMOUS")}
              >
                <BrainCircuit size={16} />
                <div>
                  <strong>AUTONOMOUS</strong>
                  <small>Mission control</small>
                </div>
              </button>
            </div>
          </section>

          {/* TELEMETRY */}
          <section className="card">
            <div className="card-title">
              <Activity size={18} />
              <span>Telemetry</span>
            </div>

            <div className="telemetry-grid">
              <Telemetry label="Altitude" value={`${drone.position.z.toFixed(1)} m`} />
              <Telemetry label="Speed" value={`${drone.speed.horizontal.toFixed(1)} m/s`} />
              <Telemetry label="Vertical" value={`${drone.velocity.z.toFixed(1)} m/s`} />
              <Telemetry label="Flight Time" value={formatFlightTime(drone.flight_time)} />
              <Telemetry label="Distance" value={`${drone.distance_travelled.toFixed(1)} m`} />
              <Telemetry label="Home Dist" value={`${drone.distance_from_home.toFixed(1)} m`} />
            </div>
          </section>

          {/* POSITION */}
          <section className="card compact">
            <div className="card-title">
              <Map size={18} />
              <span>Position</span>
            </div>

            <div className="position-display">
              <div className="pos-item">
                <span className="pos-label">X</span>
                <strong className="pos-value">{drone.position.x.toFixed(2)} m</strong>
              </div>
              <div className="pos-item">
                <span className="pos-label">Y</span>
                <strong className="pos-value">{drone.position.y.toFixed(2)} m</strong>
              </div>
              <div className="pos-item">
                <span className="pos-label">Z</span>
                <strong className="pos-value">{drone.position.z.toFixed(2)} m</strong>
              </div>
            </div>
          </section>

          {/* ALTITUDE */}
          <section className="card compact">
            <div className="card-title">
              <Mountain size={18} />
              <span>Altitude</span>
            </div>

            <div className="altitude-header">
              <strong className="altitude-current">{drone.position.z.toFixed(1)} m</strong>
              <span className="altitude-max">MAX {drone.limits.max_altitude} m</span>
            </div>

            <div className="progress">
              <div className="progress-fill" style={{ width: `${altitudePercentage}%` }} />
            </div>

            <div className="altitude-footer">
              <span>Ground</span>
              <span>{altitudePercentage.toFixed(1)}%</span>
              <span>Maximum</span>
            </div>
          </section>

          {/* BATTERY - Enhanced */}
          <section className="card compact">
            <div className="card-title">
              <Battery size={18} />
              <span>Battery</span>
            </div>

            <div className="battery-value" style={{ color: batteryColor }}>
              {drone.battery.toFixed(0)}%
            </div>

            <div className="progress">
              <div
                className="progress-fill battery-progress"
                style={{
                  width: `${drone.battery}%`,
                  background: batteryColor,
                }}
              />
            </div>

            <div className="battery-meta">
              <span>Power status</span>
              <strong>
                {drone.battery > 50 ? "NORMAL" : drone.battery > 20 ? "CAUTION" : "CRITICAL"}
              </strong>
            </div>

            <div className="battery-health">
              <span>Health</span>
              <strong className={
                batteryHealth > 80 ? "health-good" : batteryHealth > 60 ? "health-warning" : "health-critical"
              }>
                {batteryHealth.toFixed(0)}%
              </strong>
            </div>

            <div className="battery-temperature">
              <span>Temperature</span>
              <strong className={
                batteryTemp < 35 ? "temp-normal" : batteryTemp < 45 ? "temp-warm" : "temp-hot"
              }>
                <Thermometer size={12} style={{ display: 'inline', marginRight: '4px' }} />
                {batteryTemp.toFixed(1)}°C
              </strong>
            </div>
          </section>

          {/* SIGNAL */}
          <section className="card signal-card">
            <div className="card-title">
              <Signal size={18} />
              <span>Signal Status</span>
              <span className="signal-status" style={{ color: signalColor }}>
                {drone.signal?.quality || "Unknown"}
              </span>
            </div>

            <div className="signal-display">
              <div className="signal-strength-display">
                <strong>{(drone.signal?.strength || 1) * 100}</strong>
                <span>%</span>
              </div>
              <div className="signal-latency-display">
                <span>Latency</span>
                <strong>{drone.signal?.latency?.toFixed(1) || 0} ms</strong>
              </div>
              <div className="signal-distance-display">
                <span>Distance</span>
                <strong>{drone.signal?.distance?.toFixed(1) || 0} m</strong>
              </div>
            </div>

            <div className="progress">
              <div
                className="progress-fill"
                style={{
                  width: `${((drone.signal?.strength || 1) * 100)}%`,
                  background: signalColor,
                }}
              />
            </div>
          </section>

          {/* WIND */}
          <section className="card wind-card">
            <div className="card-title">
              <Wind size={18} />
              <span>Wind Conditions</span>
              <span className="wind-status" style={{ color: windColor }}>
                {drone.wind?.description || "Calm"}
              </span>
            </div>

            <div className="wind-display">
              <div className="wind-speed-display">
                <strong>{windTotal.toFixed(1)}</strong>
                <span>m/s</span>
              </div>
              
              <div className="wind-direction-display">
                <div 
                  className="wind-compass" 
                  style={{ transform: `rotate(${Math.atan2(drone.wind?.speed_y || 0, drone.wind?.speed_x || 0) * 180 / Math.PI}deg)` }}
                >
                  <ArrowUp size={20} />
                </div>
                <span>{Math.atan2(drone.wind?.speed_y || 0, drone.wind?.speed_x || 0) * 180 / Math.PI}°</span>
              </div>
              
              <div className="wind-gust-display">
                <span>Gust</span>
                <strong>{(windTotal * 0.3).toFixed(1)} m/s</strong>
              </div>
            </div>

            <div className="wind-components">
              <div>
                <span>X Component</span>
                <strong>{(drone.wind?.speed_x || 0).toFixed(1)} m/s</strong>
              </div>
              <div>
                <span>Y Component</span>
                <strong>{(drone.wind?.speed_y || 0).toFixed(1)} m/s</strong>
              </div>
            </div>

            <div className="wind-controls">
              <button className="btn-outline" onClick={() => handleSetWind(0)} style={{ fontSize: "7px" }}>
                CALM
              </button>
              <button className="btn-outline" onClick={() => handleSetWind(3)} style={{ fontSize: "7px" }}>
                MODERATE
              </button>
              <button className="btn-outline" onClick={() => handleSetWind(7)} style={{ fontSize: "7px" }}>
                STRONG
              </button>
            </div>
          </section>

          {/* MISSION */}
          <section className="card mission-card">
            <div className="card-title">
              <Route size={18} />
              <span>Mission Control</span>
              <span
                className={`mission-status ${
                  missionRunning ? (missionPaused ? "paused" : "running") : ""
                }`}
              >
                {missionRunning
                  ? missionPaused
                    ? "PAUSED"
                    : "RUNNING"
                  : drone.mission.status === "COMPLETED"
                  ? "COMPLETE"
                  : "READY"}
              </span>
            </div>

            <div className="mission-summary">
              <div>
                <span>Mission</span>
                <strong>AREA SURVEY</strong>
              </div>
              <div>
                <span>Waypoint</span>
                <strong>
                  {waypoints.length > 0 
                    ? `${Math.min(drone.mission.current_waypoint_index + 1, drone.mission.total_waypoints || waypoints.length)}/${waypoints.length}`
                    : "0/0"}
                </strong>
              </div>
              <div>
                <span>Progress</span>
                <strong>{drone.mission.progress.toFixed(0)}%</strong>
              </div>
            </div>

            <div className="mission-progress">
              <div className="progress">
                <div
                  className="progress-fill"
                  style={{ width: `${drone.mission.progress || missionProgress}%` }}
                />
              </div>
              <span>{(drone.mission.progress || missionProgress).toFixed(0)}%</span>
            </div>

            <div className="waypoint-list">
              {waypoints.length === 0 ? (
                <div className="waypoint-empty">
                  <span>No waypoints set. Click "Add WP" and click on the map to plan your mission.</span>
                </div>
              ) : (
                waypoints.map((waypoint) => (
                  <div className={`waypoint-row ${waypoint.status}`} key={waypoint.id}>
                    <span className="waypoint-number">
                      {waypoint.status === "completed" ? "✓" : waypoint.id}
                    </span>
                    <div className="waypoint-info">
                      <strong>WP{String(waypoint.id).padStart(2, "0")}</strong>
                      <small>
                        ({waypoint.x.toFixed(1)}m, {waypoint.y.toFixed(1)}m)
                      </small>
                    </div>
                    <input
                      type="number"
                      className="waypoint-alt-input"
                      value={waypoint.altitude}
                      onChange={(e) => updateWaypointAltitude(waypoint.id, parseFloat(e.target.value) || 0)}
                      min="0"
                      max="120"
                      disabled={missionRunning}
                    />
                    <span className="waypoint-alt">m</span>
                    <button
                      className="waypoint-remove"
                      onClick={() => removeWaypoint(waypoint.id)}
                      disabled={missionRunning}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="waypoint-controls">
              <button
                className={`btn-outline ${isSelectingWaypoint ? "active" : ""}`}
                onClick={() => setIsSelectingWaypoint(!isSelectingWaypoint)}
                disabled={missionRunning}
              >
                <Plus size={14} />
                {isSelectingWaypoint ? "CANCEL" : "ADD WP"}
              </button>
              <button
                className="btn-outline"
                onClick={clearWaypoints}
                disabled={missionRunning || waypoints.length === 0}
              >
                <Trash2 size={14} />
                CLEAR
              </button>
              <div className="waypoint-alt-control">
                <span>ALT</span>
                <input
                  type="number"
                  className="waypoint-alt-global"
                  value={selectedAltitude}
                  onChange={(e) => setSelectedAltitude(Math.max(0, Math.min(120, parseFloat(e.target.value) || 0)))}
                  min="0"
                  max="120"
                  disabled={missionRunning}
                />
                <span>m</span>
              </div>
            </div>

            <div className="mission-buttons">
              {!missionRunning ? (
                <button
                  className="btn-primary"
                  onClick={startMission}
                  disabled={!isFlying || waypoints.length === 0}
                >
                  <Play size={15} />
                  START MISSION
                </button>
              ) : missionPaused ? (
                <button className="btn-primary" onClick={resumeMission}>
                  <Play size={15} />
                  RESUME
                </button>
              ) : (
                <button className="btn-secondary" onClick={pauseMission}>
                  <Pause size={15} />
                  PAUSE
                </button>
              )}

              <button
                className="btn-outline"
                onClick={abortMission}
                disabled={!missionRunning}
              >
                <Square size={14} />
                ABORT
              </button>

              <button className="btn-outline" onClick={resetMission}>
                <RotateCcw size={14} />
                RESET
              </button>
            </div>
          </section>

          {/* SPEED */}
          <section className="card compact">
            <div className="card-title">
              <Gauge size={18} />
              <span>Speed Controls</span>
              {!isFlying && <span className="speed-status-badge">GROUNDED</span>}
            </div>

            <div className="speed-controls">
              <div className="speed-header">
                <div>
                  <span className="speed-label">TARGET SPEED</span>
                  <strong className="speed-value">
                    {drone.targets.speed.toFixed(1)}
                    <small> m/s</small>
                  </strong>
                </div>
                <span className="speed-max">MAX {drone.limits.max_speed} m/s</span>
              </div>

              <div className="speed-buttons">
                <button
                  className="speed-btn decrease"
                  onClick={() => sendCommand("/api/drone/speed/decrease")}
                  disabled={!isFlying}
                >
                  −
                  <span>SPEED</span>
                </button>

                <div className="speed-display">
                  <Gauge size={18} />
                  <span>{drone.targets.speed.toFixed(0)}</span>
                  <small>m/s</small>
                </div>

                <button
                  className="speed-btn increase"
                  onClick={() => sendCommand("/api/drone/speed/increase")}
                  disabled={!isFlying}
                >
                  +
                  <span>SPEED</span>
                </button>
              </div>

              {!isFlying && <div className="speed-hint">Takeoff to adjust speed</div>}
            </div>
          </section>

          {/* CONTROLS */}
          <section className="card controls-card">
            <div className="card-title">
              <Power size={18} />
              <span>Flight Controls</span>
            </div>

            <div className="primary-controls">
              <button className="btn-primary takeoff" onClick={handleTakeoff}>
                <Plane size={16} />
                TAKEOFF
              </button>
              <button className="btn-secondary land" onClick={handleLand}>
                <Navigation size={16} />
                LAND
              </button>
            </div>

            <div className="secondary-controls">
              <button className="btn-outline" onClick={handleRTH}>
                <Home size={16} />
                RTH
              </button>
              <button className="btn-danger" onClick={handleEmergency}>
                <Shield size={16} />
                EMERGENCY
              </button>
            </div>

            <div className="control-section-label">MANUAL MOVEMENT</div>

            <div className="movement-controls">
              <button
                className="move-btn move-up"
                disabled={flightMode !== "MANUAL"}
                onClick={() => sendCommand("/api/drone/move", "POST", { direction: "forward" })}
              >
                <ArrowUp size={20} />
              </button>

              <div className="move-row">
                <button
                  className="move-btn move-left"
                  disabled={flightMode !== "MANUAL"}
                  onClick={() => sendCommand("/api/drone/move", "POST", { direction: "left" })}
                >
                  <ArrowLeft size={20} />
                </button>

                <button className="move-btn stop-button" onClick={() => sendCommand("/api/drone/stop")}>
                  <div className="stop-icon" />
                </button>

                <button
                  className="move-btn move-right"
                  disabled={flightMode !== "MANUAL"}
                  onClick={() => sendCommand("/api/drone/move", "POST", { direction: "right" })}
                >
                  <ArrowRight size={20} />
                </button>
              </div>

              <button
                className="move-btn move-down"
                disabled={flightMode !== "MANUAL"}
                onClick={() => sendCommand("/api/drone/move", "POST", { direction: "backward" })}
              >
                <ArrowDown size={20} />
              </button>
            </div>

            <div className="keyboard-hint">
              <span>WASD / ARROWS</span>
              <span>SPACE = STOP</span>
              <span>F = FPV</span>
            </div>

            <div className="altitude-controls">
              <button
                className="alt-btn climb"
                onClick={() =>
                  sendCommand("/api/drone/altitude", "POST", {
                    altitude: Math.min(drone.position.z + 5, drone.limits.max_altitude),
                  })
                }
              >
                <ArrowUp size={14} />
                CLIMB
              </button>
              <button
                className="alt-btn descend"
                onClick={() =>
                  sendCommand("/api/drone/altitude", "POST", {
                    altitude: Math.max(drone.position.z - 5, 0),
                  })
                }
              >
                <ArrowDown size={14} />
                DESCEND
              </button>
            </div>

            {commandStatus && (
              <div
                className={`command-status ${
                  commandStatus.toLowerCase().includes("accepted") ||
                  commandStatus.toLowerCase().includes("started") ||
                  commandStatus.toLowerCase().includes("completed")
                    ? "success"
                    : "error"
                }`}
              >
                <span className="status-indicator" />
                {commandStatus}
              </div>
            )}
          </section>

          {/* EMERGENCY CONTROLS */}
          <section className="card emergency-card">
            <div className="card-title">
              <AlertOctagon size={18} />
              <span>Emergency</span>
              {drone.emergency?.active && (
                <span className="emergency-active">⚠️ ACTIVE</span>
              )}
            </div>

            <div className="emergency-grid">
              <button
                className="btn-danger"
                onClick={() => triggerEmergency("motor_failure")}
                style={{ fontSize: "7px" }}
              >
                MOTOR FAIL
              </button>
              <button
                className="btn-danger"
                onClick={() => triggerEmergency("gps_loss")}
                style={{ fontSize: "7px" }}
              >
                GPS LOSS
              </button>
              <button
                className="btn-danger"
                onClick={() => triggerEmergency("compass_error")}
                style={{ fontSize: "7px" }}
              >
                COMPASS ERR
              </button>
              <button
                className="btn-danger"
                onClick={() => triggerEmergency("battery_critical")}
                style={{ fontSize: "7px" }}
              >
                BATTERY CRIT
              </button>
              <button
                className="btn-danger"
                onClick={() => triggerEmergency("signal_loss")}
                style={{ fontSize: "7px" }}
              >
                SIGNAL LOSS
              </button>
              <button
                className="btn-outline"
                onClick={resolveEmergency}
                disabled={!drone.emergency?.active}
                style={{ fontSize: "7px" }}
              >
                RESOLVE
              </button>
            </div>
          </section>

          {/* RECORDING */}
          <section className="card recording-card">
            <div className="card-title">
              <Video size={18} />
              <span>Mission Recording</span>
              {isRecording && (
                <span className="recording-active">● REC</span>
              )}
              {isPlaying && (
                <span className="playback-active">▶ PLAY</span>
              )}
            </div>

            <div className="recording-controls">
              {!isRecording ? (
                <button className="btn-primary" onClick={startRecording} style={{ fontSize: "7px" }}>
                  <Video size={14} />
                  START RECORDING
                </button>
              ) : (
                <button className="btn-danger" onClick={stopRecording} style={{ fontSize: "7px" }}>
                  <StopCircle size={14} />
                  STOP RECORDING
                </button>
              )}

              <button
                className="btn-outline"
                onClick={() => setShowRecordings(!showRecordings)}
                style={{ fontSize: "7px" }}
              >
                <List size={14} />
                {showRecordings ? "HIDE" : "SHOW"} RECORDINGS
              </button>
            </div>

            {showRecordings && (
              <div className="recordings-list">
                {recordings.length === 0 ? (
                  <div className="waypoint-empty">No recordings found</div>
                ) : (
                  recordings.map((rec) => (
                    <div className="recording-item" key={rec.name}>
                      <span>{rec.name}</span>
                      <span>{rec.size_kb} KB</span>
                      <button
                        className="btn-outline"
                        onClick={() => loadRecording(rec.name)}
                        style={{ fontSize: "6px", padding: "4px" }}
                      >
                        <PlayCircle size={12} />
                        PLAY
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}

            {isPlaying && (
              <div className="playback-progress">
                <div className="progress">
                  <div
                    className="progress-fill"
                    style={{ width: `${playbackProgress * 100}%` }}
                  />
                </div>
                <button className="btn-outline" onClick={stopPlayback} style={{ fontSize: "7px" }}>
                  <StopCircle size={12} />
                  STOP PLAYBACK
                </button>
              </div>
            )}
          </section>

          {/* SIMULATION */}
          <section className="card simulation-card">
            <div className="card-title">
              <Zap size={18} />
              <span>Simulation Control</span>
            </div>

            <div className="simulation-status">
              <div>
                <span>SIMULATION</span>
                <strong>{simulationPaused ? "PAUSED" : "RUNNING"}</strong>
              </div>
              <div>
                <span>SPEED</span>
                <strong>{simulationSpeed}x</strong>
              </div>
            </div>

            <div className="simulation-buttons">
              <button className="btn-outline" onClick={() => setSimulationPaused(!simulationPaused)}>
                {simulationPaused ? <Play size={14} /> : <Pause size={14} />}
                {simulationPaused ? "RESUME" : "PAUSE"}
              </button>

              <button
                className="btn-outline"
                onClick={() => {
                  setTelemetryHistory([]);
                  setEvents([]);
                  addEvent("SYSTEM", "Telemetry history reset");
                }}
              >
                <RotateCcw size={14} />
                RESET DATA
              </button>
            </div>

            <div className="simulation-speed">
              {[0.5, 1, 2, 5].map((speed) => (
                <button
                  key={speed}
                  className={
                    simulationSpeed === speed
                      ? "simulation-speed-btn active"
                      : "simulation-speed-btn"
                  }
                  onClick={() => handleSimulationSpeedChange(speed)}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </section>

          {/* GEOFENCE */}
          <section className="card geofence-card">
            <div className="card-title">
              <Target size={18} />
              <span>Geofence</span>
              <span
                style={{
                  marginLeft: "auto",
                  color: geofenceColor,
                  fontSize: "8px",
                }}
              >
                {drone.geofence.is_breached
                  ? "BREACHED"
                  : drone.geofence.is_warning
                  ? "WARNING"
                  : "SAFE"}
              </span>
            </div>

            <div className="geofence-status">
              <div>
                <span>Radius</span>
                <strong>{drone.geofence.radius}m</strong>
              </div>
              <div>
                <span>Distance</span>
                <strong>{drone.geofence.distance_from_center.toFixed(1)}m</strong>
              </div>
              <div>
                <span>Used</span>
                <strong style={{ color: geofenceColor }}>
                  {drone.geofence.distance_percentage.toFixed(0)}%
                </strong>
              </div>
            </div>

            <div className="progress">
              <div
                className="progress-fill"
                style={{
                  width: `${Math.min(drone.geofence.distance_percentage, 100)}%`,
                  background: geofenceColor,
                }}
              />
            </div>

            <div className="geofence-controls">
              <button
                className="btn-outline"
                onClick={() => handleSetGeofence(50)}
                style={{ fontSize: "7px" }}
              >
                SET 50m
              </button>
              <button
                className="btn-outline"
                onClick={() => handleSetGeofence(100)}
                style={{ fontSize: "7px" }}
              >
                SET 100m
              </button>
              <button
                className="btn-outline"
                onClick={() => handleSetGeofence(200)}
                style={{ fontSize: "7px" }}
              >
                SET 200m
              </button>
            </div>
          </section>

          {/* AI */}
          <section className="card ai-card">
            <div className="card-title">
              <BrainCircuit size={18} />
              <span>AI Flight Analytics</span>
              <span className="ai-beta">SIM</span>
            </div>

            <div className="ai-risk">
              <div>
                <span className="ai-label">FLIGHT RISK</span>
                <strong className={`risk-${aiRisk.toLowerCase()}`}>{aiRisk}</strong>
              </div>
              <div className="anomaly-score">
                <span>ANOMALY SCORE</span>
                <strong>{aiAnomalyScore.toFixed(2)}</strong>
              </div>
            </div>

            <div className="ai-bars">
              <AiBar
                label="Flight Stability"
                value={Math.max(0, 100 - Math.abs(drone.velocity.z) * 10)}
              />
              <AiBar label="Battery Health" value={drone.battery} />
              <AiBar
                label="Navigation Confidence"
                value={flightMode === "AUTONOMOUS" ? 94 : 87}
              />
              <AiBar
                label="Geofence Safety"
                value={Math.max(0, 100 - drone.geofence.distance_percentage)}
              />
              <AiBar
                label="Signal Quality"
                value={((drone.signal?.strength || 1) * 100)}
              />
            </div>

            <div className="ai-prediction">
              <div className="prediction-icon">
                <BrainCircuit size={16} />
              </div>
              <div>
                <span>CURRENT PREDICTION</span>
                <strong>
                  {drone.emergency?.active
                    ? "⚠️ EMERGENCY"
                    : aiRisk === "LOW"
                    ? "NORMAL FLIGHT"
                    : drone.geofence.is_breached
                    ? "GEOFENCE BREACH"
                    : "POTENTIAL ANOMALY"}
                </strong>
              </div>
              <ChevronRight size={15} />
            </div>
          </section>
        </aside>
      </main>

      {/* =====================================================
          FPV CAMERA OVERLAY
      ===================================================== */}

      {showFPV && drone && (
        <div className={`fpv-camera ${fpvFullscreen ? 'fpv-fullscreen' : ''}`}>
          <div className="fpv-header">
            <div className="fpv-title">
              <Camera size={16} />
              <span>FPV Camera</span>
              <span className="fpv-recording">{fpvRecording ? '● REC' : ''}</span>
              {drone.emergency?.active && (
                <span className="fpv-emergency">⚠️ EMERGENCY</span>
              )}
            </div>
            <div className="fpv-controls">
              <button onClick={() => setFpvZoom(z => Math.min(z * 1.2, 3))} title="Zoom In">
                <Maximize2 size={14} />
              </button>
              <button onClick={() => setFpvZoom(z => Math.max(z / 1.2, 0.5))} title="Zoom Out">
                <Minimize2 size={14} />
              </button>
              <button onClick={() => setFpvRecording(!fpvRecording)} title="Record">
                <Video size={14} style={{ color: fpvRecording ? '#ff4444' : '#aeb9c0' }} />
              </button>
              <button onClick={() => setFpvFullscreen(!fpvFullscreen)} title="Toggle Fullscreen">
                {fpvFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
              </button>
              <button onClick={() => setShowFPV(false)} title="Close">
                ✕
              </button>
            </div>
          </div>
          <canvas
            ref={fpvCanvasRef}
            width={640}
            height={480}
            className="fpv-canvas"
          />
          <div className="fpv-overlay">
            <div className="fpv-telemetry">
              <div>
                <span>ALT</span>
                <strong>{drone.position.z.toFixed(1)}m</strong>
              </div>
              <div>
                <span>SPD</span>
                <strong>{drone.speed.horizontal.toFixed(1)}m/s</strong>
              </div>
              <div>
                <span>BAT</span>
                <strong style={{ color: batteryColor }}>
                  {drone.battery.toFixed(0)}%
                </strong>
              </div>
              <div>
                <span>SIG</span>
                <strong style={{ color: signalColor }}>
                  {((drone.signal?.strength || 1) * 100).toFixed(0)}%
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// COMPONENTS
// ============================================================

function Telemetry({ label, value }: { label: string; value: string }) {
  return (
    <div className="telemetry-item">
      <span className="telemetry-label">{label}</span>
      <strong className="telemetry-value">{value}</strong>
    </div>
  );
}

function OverlayMetric({
  label,
  value,
  unit,
  valueColor,
}: {
  label: string;
  value: string;
  unit?: string;
  valueColor?: string;
}) {
  return (
    <div className="overlay-item">
      <span className="overlay-label">{label}</span>
      <strong className="overlay-value" style={{ color: valueColor }}>
        {value}
        {unit && <small> {unit}</small>}
      </strong>
    </div>
  );
}

function MiniHealth({
  icon,
  label,
  active,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
}) {
  return (
    <div className="mini-health">
      {icon}
      <span>{label}</span>
      <i className={active ? "online" : "offline"} />
    </div>
  );
}

function HealthItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  const isWarning = value === "LOST" || value === "LOW";
  const isCritical = value === "CRITICAL";
  
  return (
    <div className="health-item">
      <div className="health-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong style={{ color: isCritical ? '#ef4444' : isWarning ? '#fbbf24' : '#00d084' }}>
          {value}
        </strong>
      </div>
      <span className="health-dot" style={{ 
        background: isCritical ? '#ef4444' : isWarning ? '#fbbf24' : '#00d084',
        boxShadow: isCritical ? '0 0 8px rgba(239, 68, 68, 0.7)' : isWarning ? '0 0 8px rgba(251, 191, 36, 0.7)' : '0 0 8px rgba(0, 208, 132, 0.7)'
      }} />
    </div>
  );
}

function AiBar({ label, value }: { label: string; value: number }) {
  const safeValue = Math.max(0, Math.min(100, value));

  return (
    <div className="ai-bar">
      <div className="ai-bar-header">
        <span>{label}</span>
        <strong>{safeValue.toFixed(0)}%</strong>
      </div>
      <div className="progress">
        <div className="progress-fill" style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}

function Trajectory({
  history,
  drone,
}: {
  history: TelemetryPoint[];
  drone: DroneStatus;
}) {
  if (history.length < 2) return null;

  return (
    <div className="trajectory-indicator">
      <Route size={13} />
      <span>TRAJECTORY ACTIVE</span>
      <strong>{drone.distance_travelled.toFixed(1)}m</strong>
    </div>
  );
}

function TelemetryGraph({ history }: { history: TelemetryPoint[] }) {
  if (history.length < 2) {
    return <div className="graph-empty">Waiting for telemetry history...</div>;
  }

  const width = 600;
  const height = 190;

  const altitudes = history.map((point) => point.altitude);
  const speeds = history.map((point) => point.speed);

  const maxAltitude = Math.max(10, ...altitudes);
  const maxSpeed = Math.max(10, ...speeds);

  const altitudePoints = history
    .map((point, index) => {
      const x = (index / (history.length - 1)) * width;
      const y = height - (point.altitude / maxAltitude) * height;
      return `${x},${y}`;
    })
    .join(" ");

  const speedPoints = history
    .map((point, index) => {
      const x = (index / (history.length - 1)) * width;
      const y = height - (point.speed / maxSpeed) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="telemetry-graph">
      <div className="graph-legend">
        <span>
          <i className="legend-altitude" />
          Altitude
        </span>
        <span>
          <i className="legend-speed" />
          Speed
        </span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        {[0, 1, 2, 3, 4].map((line) => (
          <line
            key={line}
            x1="0"
            x2={width}
            y1={(height / 4) * line}
            y2={(height / 4) * line}
            className="graph-grid-line"
          />
        ))}

        <polyline points={altitudePoints} className="graph-altitude-line" fill="none" />
        <polyline points={speedPoints} className="graph-speed-line" fill="none" />
      </svg>

      <div className="graph-labels">
        <span>NOW</span>
        <span>−20s</span>
        <span>−40s</span>
      </div>
    </div>
  );
}

// ============================================================
// UTILITIES - Already defined at the top
// ============================================================

export default App;