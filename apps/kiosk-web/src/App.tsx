import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { ShieldCheck, Wifi, Clock, Maximize2, Minimize2, RefreshCw, Smartphone } from 'lucide-react';
import { useDynamicQR } from './hooks/useDynamicQR.ts';

export default function App() {
  const { qrPayloadString, officeName, tenantName, secondsRemaining, isConnected } = useDynamicQR();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Live Clock updater
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  const progressPercentage = ((15 - secondsRemaining) / 15) * 100;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      background: 'radial-gradient(ellipse at 50% 20%, #172554 0%, #090d16 70%)',
      padding: '24px 32px',
      justifyContent: 'space-between',
    }}>
      {/* Top Navigation Bar */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.7)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '16px 28px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            padding: '10px 14px',
            borderRadius: '12px',
            fontWeight: 800,
            fontSize: '20px',
            letterSpacing: '1px',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <ShieldCheck size={24} />
            ZuiGO
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc' }}>{tenantName}</h1>
            <p style={{ fontSize: '13px', color: '#94a3b8' }}>📍 {officeName}</p>
          </div>
        </div>

        {/* Live Clock & Connection Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: isConnected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)',
            border: `1px solid ${isConnected ? 'rgba(34, 197, 94, 0.4)' : 'rgba(234, 179, 8, 0.4)'}`,
            padding: '6px 14px',
            borderRadius: '999px',
            fontSize: '13px',
            fontWeight: 600,
            color: isConnected ? '#4ade80' : '#fde047',
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isConnected ? '#22c55e' : '#eab308',
              boxShadow: isConnected ? '0 0 10px #22c55e' : 'none',
            }} />
            {isConnected ? 'Terminal Live' : 'Offline Buffer'}
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '20px',
            fontWeight: 700,
            color: '#e2e8f0',
          }}>
            <Clock size={20} color="#60a5fa" />
            {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </div>

          <button
            onClick={toggleFullscreen}
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#cbd5e1',
              padding: '10px',
              borderRadius: '12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
            title="Toggle Fullscreen (F)"
          >
            {isFullscreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
          </button>
        </div>
      </header>

      {/* Main Center Stage: Dynamic QR Display */}
      <main style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '24px 0',
      }}>
        <div style={{
          position: 'relative',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(96, 165, 250, 0.3)',
          borderRadius: '32px',
          padding: '36px',
          boxShadow: '0 25px 60px -15px rgba(30, 58, 138, 0.5), 0 0 50px rgba(59, 130, 246, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: '480px',
          width: '100%',
        }}>
          {/* Badge */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(59, 130, 246, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            color: '#93c5fd',
            padding: '6px 14px',
            borderRadius: '999px',
            fontSize: '12px',
            fontWeight: 700,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
            marginBottom: '24px',
          }}>
            <RefreshCw size={14} className="animate-spin" />
            Dynamic Anti-Proxy Token
          </div>

          {/* QR Code Canvas Card */}
          <div style={{
            background: '#ffffff',
            padding: '24px',
            borderRadius: '24px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            {qrPayloadString ? (
              <QRCodeSVG
                value={qrPayloadString}
                size={280}
                level="M"
                includeMargin={false}
              />
            ) : (
              <div style={{ width: 280, height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                Initializing...
              </div>
            )}
          </div>

          {/* 15-Second Animated Progress Bar */}
          <div style={{ width: '100%', marginTop: '28px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px',
              fontSize: '13px',
              color: '#94a3b8',
              fontWeight: 500,
            }}>
              <span>Code Security Rotation</span>
              <span style={{
                fontFamily: 'JetBrains Mono, monospace',
                color: secondsRemaining <= 3 ? '#ef4444' : '#60a5fa',
                fontWeight: 700,
              }}>
                Refreshes in {secondsRemaining}s
              </span>
            </div>

            <div style={{
              width: '100%',
              height: '8px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '999px',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${100 - progressPercentage}%`,
                height: '100%',
                background: secondsRemaining <= 3
                  ? 'linear-gradient(90deg, #ef4444, #f97316)'
                  : 'linear-gradient(90deg, #3b82f6, #60a5fa)',
                transition: 'width 1s linear',
                borderRadius: '999px',
              }} />
            </div>
          </div>
        </div>
      </main>

      {/* Footer Instructions for Employees */}
      <footer style={{
        background: 'rgba(15, 23, 42, 0.6)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: '20px',
        padding: '18px 32px',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '10px', borderRadius: '12px', color: '#60a5fa' }}>
            <Smartphone size={22} />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>Step 1: Open Mobile App</div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Connect to office Wi-Fi network</div>
          </div>
        </div>

        <div style={{ width: '1px', height: '36px', background: 'rgba(255, 255, 255, 0.1)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '10px', borderRadius: '12px', color: '#60a5fa' }}>
            <RefreshCw size={22} />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>Step 2: Scan Dynamic QR</div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Point camera at this laptop screen</div>
          </div>
        </div>

        <div style={{ width: '1px', height: '36px', background: 'rgba(255, 255, 255, 0.1)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(34, 197, 94, 0.2)', padding: '10px', borderRadius: '12px', color: '#4ade80' }}>
            <ShieldCheck size={22} />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>Step 3: 1-Sec Face Liveness</div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Zero-trust hardware-free confirmation</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
