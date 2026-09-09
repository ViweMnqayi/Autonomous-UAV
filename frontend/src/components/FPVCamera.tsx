import { useEffect, useRef, useState } from 'react';
import { Camera, Maximize2, Minimize2, RotateCcw, Crosshair } from 'lucide-react';

interface FPVCameraProps {
  drone: any;
  isVisible: boolean;
  onClose: () => void;
}

export function FPVCamera({ drone, isVisible, onClose }: FPVCameraProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [tiltAngle, setTiltAngle] = useState(0);
  const [panAngle, setPanAngle] = useState(0);
  const [recording, setRecording] = useState(false);

  useEffect(() => {
    if (!isVisible || !canvasRef.current || !drone) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Animation loop for FPV view
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

      // Ground
      const groundY = height * 0.6 + (drone.position.z / 50) * height * 0.2;
      ctx.fillStyle = '#5a684f';
      ctx.fillRect(0, groundY, width, height - groundY);

      // Grid
      ctx.strokeStyle = 'rgba(255,255,255,0.1)';
      ctx.lineWidth = 1;
      const gridSize = 40 * zoom;
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

      // Horizon line
      ctx.strokeStyle = 'rgba(255,255,255,0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, groundY);
      ctx.lineTo(width, groundY);
      ctx.stroke();

      // HUD
      drawHUD(ctx, width, height, drone);

      // Crosshair
      drawCrosshair(ctx, width, height);

      // Signal and battery indicators
      drawIndicators(ctx, width, height, drone);

      animationId = requestAnimationFrame(renderFPV);
    };

    renderFPV();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [drone, isVisible, zoom]);

  const drawHUD = (ctx: CanvasRenderingContext2D, width: number, height: number, drone: any) => {
    const margin = 20;
    ctx.fillStyle = 'rgba(0,255,0,0.8)';
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
    ctx.fillText(`HDG 045°`, margin, margin + 55);

    // Distance
    ctx.fillStyle = '#ff88ff';
    ctx.fillText(`DIST ${drone.distance_from_home.toFixed(1)}m`, margin, margin + 75);

    // Battery
    const batteryColor = drone.battery > 50 ? '#00ff88' : drone.battery > 20 ? '#ffaa00' : '#ff4444';
    ctx.fillStyle = batteryColor;
    ctx.fillText(`BAT ${drone.battery.toFixed(0)}%`, margin, margin + 95);
  };

  const drawCrosshair = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
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
  };

  const drawIndicators = (ctx: CanvasRenderingContext2D, width: number, height: number, drone: any) => {
    const margin = 20;
    const x = width - margin;

    // Signal indicator
    const signalBars = 4;
    const barWidth = 6;
    const barSpacing = 4;
    const barHeight = 16;
    const signalStrength = drone.signal?.strength || 1;

    for (let i = 0; i < signalBars; i++) {
      const barX = x - (signalBars - i) * (barWidth + barSpacing);
      const barHeightFilled = (i + 1) / signalBars * barHeight;
      const isActive = signalStrength > (i / signalBars);

      ctx.fillStyle = isActive ? '#00ff88' : 'rgba(255,255,255,0.2)';
      ctx.fillRect(barX, margin, barWidth, barHeightFilled);
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`fpv-camera ${isFullscreen ? 'fpv-fullscreen' : ''}`}>
      <div className="fpv-header">
        <div className="fpv-title">
          <Camera size={16} />
          <span>FPV Camera</span>
          <span className="fpv-recording">{recording ? '● REC' : ''}</span>
        </div>
        <div className="fpv-controls">
          <button onClick={() => setZoom(z => Math.min(z * 1.2, 3))} title="Zoom In">
            <Maximize2 size={14} />
          </button>
          <button onClick={() => setZoom(z => Math.max(z / 1.2, 0.5))} title="Zoom Out">
            <Minimize2 size={14} />
          </button>
          <button onClick={() => setRecording(!recording)} title="Record">
            <RotateCcw size={14} style={{ color: recording ? '#ff4444' : '#aeb9c0' }} />
          </button>
          <button onClick={onClose} title="Close">
            ✕
          </button>
        </div>
      </div>
      <canvas
        ref={canvasRef}
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
            <strong style={{ color: drone.battery > 50 ? '#4ade80' : drone.battery > 20 ? '#fbbf24' : '#ef4444' }}>
              {drone.battery.toFixed(0)}%
            </strong>
          </div>
        </div>
      </div>
    </div>
  );
}