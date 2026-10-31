import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { apiRequest } from '../services/api';
import { captureLocationWithAntiSpoof, captureNetworkDetails } from '../services/networkDetector';

export interface ActiveTaskTimer {
  entryId: string;
  taskId: string;
  taskTitle: string;
  startTime: Date;
}

export interface ActiveTravelShift {
  travelLogId: string;
  transportMode: string;
  odometerStartKm?: number;
  startTime: Date;
}

interface AttendanceContextType {
  isClockedIn: boolean;
  attendanceId: string | null;
  clockInTime: string | null;
  officeName: string | null;
  networkType: string;
  isOfficeWifi: boolean;
  lastPingTime: Date | null;
  setClockInSuccess: (id: string, time: string, office: string, netType?: string, isWifi?: boolean) => void;
  setClockOutSuccess: () => void;
  
  // Task Timer State
  activeTimer: ActiveTaskTimer | null;
  startTaskTimer: (entryId: string, taskId: string, taskTitle: string) => void;
  stopTaskTimer: () => void;

  // Field Travel Shift State
  activeTravelShift: ActiveTravelShift | null;
  startTravelShift: (logId: string, mode: string, odoKm?: number) => void;
  endTravelShift: () => void;

  // Live Location Telemetry Heartbeat
  sendLocationPing: (overrideNetType?: string) => Promise<void>;
}

const AttendanceContext = createContext<AttendanceContextType>({} as AttendanceContextType);

export const AttendanceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isClockedIn, setIsClockedIn] = useState(false);
  const [attendanceId, setAttendanceId] = useState<string | null>(null);
  const [clockInTime, setClockInTime] = useState<string | null>(null);
  const [officeName, setOfficeName] = useState<string | null>(null);
  const [networkType, setNetworkType] = useState<string>('OFFICE_WIFI');
  const [isOfficeWifi, setIsOfficeWifi] = useState<boolean>(true);
  const [lastPingTime, setLastPingTime] = useState<Date | null>(null);

  const [activeTimer, setActiveTimer] = useState<ActiveTaskTimer | null>(null);
  const [activeTravelShift, setActiveTravelShift] = useState<ActiveTravelShift | null>(null);

  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const setClockInSuccess = (
    id: string,
    time: string,
    office: string,
    netType: string = 'OFFICE_WIFI',
    isWifi: boolean = true
  ) => {
    setIsClockedIn(true);
    setAttendanceId(id);
    setClockInTime(time);
    setOfficeName(office);
    setNetworkType(netType);
    setIsOfficeWifi(isWifi);
  };

  const setClockOutSuccess = () => {
    setIsClockedIn(false);
    setAttendanceId(null);
    setClockInTime(null);
    setOfficeName(null);
    setActiveTimer(null); // Auto-stops active task timer upon clock-out
  };

  const startTaskTimer = (entryId: string, taskId: string, taskTitle: string) => {
    setActiveTimer({
      entryId,
      taskId,
      taskTitle,
      startTime: new Date(),
    });
  };

  const stopTaskTimer = () => {
    setActiveTimer(null);
  };

  const startTravelShift = (logId: string, mode: string, odoKm?: number) => {
    setActiveTravelShift({
      travelLogId: logId,
      transportMode: mode,
      odometerStartKm: odoKm,
      startTime: new Date(),
    });
  };

  const endTravelShift = () => {
    setActiveTravelShift(null);
  };

  // Live Location Telemetry Heartbeat Ping to Backend & Admin Panel
  const sendLocationPing = async (overrideNetType?: string) => {
    try {
      const loc = await captureLocationWithAntiSpoof();
      const net = await captureNetworkDetails();
      const effectiveNet = overrideNetType || networkType;

      await apiRequest('/attendance/ping-location', {
        method: 'POST',
        body: JSON.stringify({
          latitude: loc.latitude,
          longitude: loc.longitude,
          accuracy_meters: loc.accuracy || 12.0,
          is_mock: loc.isMock,
          network_type: effectiveNet,
          wifi_bssid: effectiveNet === 'OFFICE_WIFI' ? net.wifiBssid : null,
        }),
      });

      setLastPingTime(new Date());
    } catch (err) {
      // Telemetry heartbeat fails gracefully if offline
    }
  };

  // Periodic Telemetry Heartbeat while Clocked In (Every 25 seconds)
  useEffect(() => {
    if (isClockedIn) {
      sendLocationPing();
      pingIntervalRef.current = setInterval(() => {
        sendLocationPing();
      }, 25000);
    } else {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    }

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [isClockedIn, networkType]);

  return (
    <AttendanceContext.Provider value={{
      isClockedIn,
      attendanceId,
      clockInTime,
      officeName,
      networkType,
      isOfficeWifi,
      lastPingTime,
      setClockInSuccess,
      setClockOutSuccess,
      activeTimer,
      startTaskTimer,
      stopTaskTimer,
      activeTravelShift,
      startTravelShift,
      endTravelShift,
      sendLocationPing,
    }}>
      {children}
    </AttendanceContext.Provider>
  );
};

export const useAttendance = () => useContext(AttendanceContext);
