import { useState, useEffect, useRef } from 'react';

export interface DynamicQRData {
  t_id: string;
  o_id: string;
  ts: number;
  nonce: string;
  sig: string;
  ttl: number;
}

export interface KioskState {
  qrData: DynamicQRData | null;
  qrPayloadString: string;
  officeName: string;
  tenantName: string;
  secondsRemaining: number;
  isConnected: boolean;
  lastUpdated: Date;
}

export function useDynamicQR(kioskKey: string = 'demo-office-key') {
  const [state, setState] = useState<KioskState>({
    qrData: null,
    qrPayloadString: '',
    officeName: 'Corporate Headquarters',
    tenantName: 'ZuiGO Technologies',
    secondsRemaining: 15,
    isConnected: true,
    lastUpdated: new Date(),
  });

  const timerRef = useRef<number | null>(null);

  // Generate or fetch QR code
  const fetchNewQR = async () => {
    try {
      const response = await fetch(`/api/v1/kiosk/current-qr?kiosk_key=${kioskKey}`);
      if (response.ok) {
        const json = await response.json();
        const payloadStr = JSON.stringify(json.data);
        setState((prev) => ({
          ...prev,
          qrData: json.data,
          qrPayloadString: payloadStr,
          officeName: json.office_name,
          tenantName: json.tenant_name,
          secondsRemaining: json.data.ttl || 15,
          isConnected: true,
          lastUpdated: new Date(),
        }));
        return;
      }
    } catch {
      // Offline fallback generator so terminal never goes black
    }

    // Local deterministic generator fallback for kiosk display when offline
    const now = Math.floor(Date.now() / 1000);
    const mockData: DynamicQRData = {
      t_id: 'c7e8e58a-3642-4f30-8025-4b0717fb0534',
      o_id: 'd1e7c53a-4421-4f11-8933-4b0717fb0112',
      ts: now,
      nonce: Math.random().toString(36).substring(2, 18),
      sig: 'simulated_hmac_sha256_' + Math.random().toString(36).substring(2, 10),
      ttl: 15,
    };

    setState((prev) => ({
      ...prev,
      qrData: mockData,
      qrPayloadString: JSON.stringify(mockData),
      secondsRemaining: 15,
      isConnected: false,
      lastUpdated: new Date(),
    }));
  };

  useEffect(() => {
    fetchNewQR();

    // 1-second tick for the countdown bar
    timerRef.current = window.setInterval(() => {
      setState((prev) => {
        if (prev.secondsRemaining <= 1) {
          fetchNewQR();
          return { ...prev, secondsRemaining: 15 };
        }
        return { ...prev, secondsRemaining: prev.secondsRemaining - 1 };
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [kioskKey]);

  return state;
}
