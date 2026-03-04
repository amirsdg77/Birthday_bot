import { useEffect, useRef, useState } from "react";
import bdaySong from "./bday_song.mp3";

// ─── Fireworks canvas ─────────────────────────────────────────────────────────

function Fireworks({ duration = 8000 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const particles = [];
    const colors = ["#f48fb1", "#ce93d8", "#ff80ab", "#ea80fc", "#ffb74d", "#fff176", "#80deea"];

    function spawnBurst() {
      const x = Math.random() * canvas.width;
      const y = Math.random() * canvas.height * 0.6;
      const count = 60 + Math.floor(Math.random() * 40);
      for (let i = 0; i < count; i++) {
        const angle = (Math.PI * 2 * i) / count;
        const speed = 2 + Math.random() * 4;
        particles.push({
          x, y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          alpha: 1,
          color: colors[Math.floor(Math.random() * colors.length)],
          size: 2 + Math.random() * 3,
          decay: 0.012 + Math.random() * 0.01,
        });
      }
    }

    // Burst every 600ms
    spawnBurst();
    const burstInterval = setInterval(spawnBurst, 600);

    let animId;
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.06; // gravity
        p.alpha -= p.decay;
        if (p.alpha <= 0) { particles.splice(i, 1); continue; }
        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
      animId = requestAnimationFrame(draw);
    }
    draw();

    const stopTimer = setTimeout(() => {
      clearInterval(burstInterval);
      // Let remaining particles fade out naturally then stop
      setTimeout(() => cancelAnimationFrame(animId), 3000);
    }, duration);

    return () => {
      clearInterval(burstInterval);
      clearTimeout(stopTimer);
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, [duration]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0, left: 0,
        width: "100vw", height: "100vh",
        pointerEvents: "none",
        zIndex: 999,
      }}
    />
  );
}

// ─── Cake overlay ─────────────────────────────────────────────────────────────

function CakeOverlay({ onDone }) {
  return (
    <div className="cake-overlay" onClick={onDone}>
      <div className="cake-box">
        <div className="cake-emoji">🎂</div>
        <div className="cake-text">Happy Birthday Orgese! 🎉</div>
        <div className="cake-sub">tap to continue</div>
      </div>
    </div>
  );
}

// ─── Main BirthdayEffects ─────────────────────────────────────────────────────

export default function BirthdayEffects() {
  const [showCake, setShowCake] = useState(true);
  const audioRef = useRef(null);

  useEffect(() => {
    // Auto-play music (browsers may block autoplay — we try anyway)
    const audio = new Audio(bdaySong);
    audio.volume = 0.5;
    audio.loop = false;
    audioRef.current = audio;
    audio.play().catch(() => {
      // Autoplay blocked — play on first user interaction
      const playOnce = () => {
        audio.play().catch(() => {});
        window.removeEventListener("click", playOnce);
        window.removeEventListener("keydown", playOnce);
      };
      window.addEventListener("click", playOnce);
      window.addEventListener("keydown", playOnce);
    });

    return () => {
      audio.pause();
      audio.src = "";
    };
  }, []);

  return (
    <>
      <Fireworks duration={10000} />
      {showCake && <CakeOverlay onDone={() => setShowCake(false)} />}
    </>
  );
}
