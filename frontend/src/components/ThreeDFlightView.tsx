import { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Html, Sphere, Box, Line } from '@react-three/drei';
import * as THREE from 'three';

interface DroneStatus {
  position: { x: number; y: number; z: number };
  state: string;
  tilt?: { roll: number; pitch: number };
}

interface Waypoint {
  id: number;
  x: number;
  y: number;
  altitude: number;
  status: "pending" | "active" | "completed";
}

interface ThreeDFlightViewProps {
  drone: DroneStatus;
  waypoints: Waypoint[];
  history: Array<{ x: number; y: number; z: number }>;
  geofenceRadius: number;
}

function DroneModel({ position, tilt }: { position: { x: number; y: number; z: number }; tilt?: { roll: number; pitch: number } }) {
  const droneRef = useRef<THREE.Group>(null);
  const targetPosition = new THREE.Vector3();
  
  useFrame(() => {
    if (droneRef.current) {
      // Smooth follow the drone position
      targetPosition.set(position.x, position.z, position.y);
      droneRef.current.position.lerp(targetPosition, 0.1);
      
      // Apply tilt
      droneRef.current.rotation.x = THREE.MathUtils.degToRad(tilt?.pitch || 0);
      droneRef.current.rotation.z = THREE.MathUtils.degToRad(tilt?.roll || 0);
    }
  });
  
  return (
    <group ref={droneRef}>
      {/* Main body */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[0.6, 0.15, 0.4]} />
        <meshStandardMaterial color="#00d084" metalness={0.3} roughness={0.7} />
      </mesh>
      
      {/* Arms */}
      {[
        [-0.6, 0, -0.4],
        [-0.6, 0, 0.4],
        [0.6, 0, -0.4],
        [0.6, 0, 0.4]
      ].map((pos, i) => (
        <mesh key={i} position={[pos[0], pos[1], pos[2]]}>
          <boxGeometry args={[0.5, 0.05, 0.05]} />
          <meshStandardMaterial color="#888888" metalness={0.5} roughness={0.5} />
        </mesh>
      ))}
      
      {/* Motors */}
      {[
        [-0.85, 0, -0.45],
        [-0.85, 0, 0.45],
        [0.85, 0, -0.45],
        [0.85, 0, 0.45]
      ].map((pos, i) => (
        <mesh key={i} position={[pos[0], pos[1], pos[2]]}>
          <sphereGeometry args={[0.08]} />
          <meshStandardMaterial color="#444444" metalness={0.8} roughness={0.2} />
        </mesh>
      ))}
      
      {/* Glow effect */}
      <pointLight position={[0, 0.5, 0]} intensity={1} color="#00d084" />
    </group>
  );
}

function WaypointMarkers({ waypoints }: { waypoints: Waypoint[] }) {
  return (
    <>
      {waypoints.map((wp) => (
        <group key={wp.id} position={[wp.x, wp.altitude, wp.y]}>
          <mesh position={[0, 0, 0]}>
            <sphereGeometry args={[0.3]} />
            <meshStandardMaterial 
              color={wp.status === 'active' ? '#00d084' : wp.status === 'completed' ? '#888888' : '#4a9eff'}
              transparent 
              opacity={wp.status === 'pending' ? 0.6 : 1}
              emissive={wp.status === 'active' ? '#00d084' : '#000000'}
              emissiveIntensity={wp.status === 'active' ? 0.5 : 0}
            />
          </mesh>
          {/* Pillar */}
          <mesh position={[0, -wp.altitude/2, 0]}>
            <boxGeometry args={[0.05, wp.altitude, 0.05]} />
            <meshStandardMaterial color="#666666" transparent opacity={0.3} />
          </mesh>
          {/* Label */}
          <Html position={[0, 0.5, 0]} center>
            <div style={{
              color: 'white',
              fontSize: '10px',
              background: 'rgba(0,0,0,0.7)',
              padding: '2px 6px',
              borderRadius: '4px',
              fontFamily: 'monospace'
            }}>
              WP{String(wp.id).padStart(2, '0')}
            </div>
          </Html>
        </group>
      ))}
    </>
  );
}

function Geofence({ radius }: { radius: number }) {
  const segments = 64;
  const points: THREE.Vector3[] = [];
  
  for (let i = 0; i <= segments; i++) {
    const theta = (i / segments) * Math.PI * 2;
    points.push(new THREE.Vector3(
      Math.cos(theta) * radius,
      0,
      Math.sin(theta) * radius
    ));
  }
  
  return (
    <Line
      points={points}
      color="#00d084"
      transparent
      opacity={0.3}
      lineWidth={1}
    />
  );
}

function Terrain({ drone }: { drone: DroneStatus }) {
  const size = 200;
  const segments = 50;
  
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]}>
      <planeGeometry args={[size, size, segments, segments]} />
      <meshStandardMaterial 
        color="#1a2a1a" 
        wireframe 
        transparent 
        opacity={0.1}
      />
    </mesh>
  );
}

function FlightPath({ history }: { history: Array<{ x: number; y: number; z: number }> }) {
  if (history.length < 2) return null;
  
  const points = history.map(p => new THREE.Vector3(p.x, p.z, p.y));
  
  return (
    <Line
      points={points}
      color="#00d084"
      transparent
      opacity={0.5}
      lineWidth={1}
    />
  );
}

function CameraFollow({ target, offset }: { target: { x: number; y: number; z: number }; offset?: { x: number; y: number; z: number } }) {
  const { camera } = useThree();
  const targetPos = new THREE.Vector3(target.x, target.z, target.y);
  const offsetVec = new THREE.Vector3(offset?.x || 15, offset?.y || 10, offset?.z || 15);
  
  useFrame(() => {
    // Calculate desired camera position
    const desiredPosition = targetPos.clone().add(offsetVec);
    camera.position.lerp(desiredPosition, 0.05);
    camera.lookAt(targetPos);
  });
  
  return null;
}

export function ThreeDFlightView({ 
  drone, 
  waypoints, 
  history, 
  geofenceRadius 
}: ThreeDFlightViewProps) {
  const [isReady, setIsReady] = useState(false);
  
  useEffect(() => {
    setIsReady(true);
  }, []);
  
  if (!isReady || !drone) return null;
  
  const cameraOffset = { x: 15, y: 12, z: 15 };
  
  return (
    <div style={{ width: '100%', height: '100%', background: '#0a1219' }}>
      <Canvas shadows camera={{ position: [15, 12, 15], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 20, 10]} intensity={1} castShadow />
        <pointLight position={[0, 20, 0]} intensity={0.5} />
        
        <CameraFollow target={drone.position} offset={cameraOffset} />
        
        {/* Sky */}
        <color attach="background" args={['#1a2a3a']} />
        
        {/* Ground */}
        <Terrain drone={drone} />
        
        {/* Geofence */}
        <Geofence radius={geofenceRadius} />
        
        {/* Flight path */}
        <FlightPath history={history} />
        
        {/* Waypoints */}
        <WaypointMarkers waypoints={waypoints} />
        
        {/* Drone */}
        <DroneModel position={drone.position} tilt={drone.tilt} />
        
        {/* Grid helper */}
        <gridHelper args={[100, 20, '#00d084', '#00d084']} position={[0, 0, 0]} />
        
        <OrbitControls 
          enableDamping 
          dampingFactor={0.05}
          minDistance={5}
          maxDistance={50}
          target={[drone.position.x, drone.position.z, drone.position.y] as [number, number, number]}
        />
      </Canvas>
    </div>
  );
}