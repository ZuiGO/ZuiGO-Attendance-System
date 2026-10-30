import React, { createContext, useContext, useState, useEffect } from 'react';

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
  setClockInSuccess: (id: string, time: string, office: string) => void;
  setClockOutSuccess: () => void;
  
  // Task Timer State
  activeTimer: ActiveTaskTimer | null;
  startTaskTimer: (entryId: string, taskId: string, taskTitle: string) => void;
  stopTaskTimer: () => void;

  // Field Travel Shift State
  activeTravelShift: ActiveTravelShift | null;
  startTravelShift: (logId: string, mode: string, odoKm?: number) => void;
  endTravelShift: () => void;
}

const AttendanceContext = createContext<AttendanceContextType>({} as AttendanceContextType);

export const AttendanceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isClockedIn, setIsClockedIn] = useState(false);
  const [attendanceId, setAttendanceId] = useState<string | null>(null);
  const [clockInTime, setClockInTime] = useState<string | null>(null);
  const [officeName, setOfficeName] = useState<string | null>(null);

  const [activeTimer, setActiveTimer] = useState<ActiveTaskTimer | null>(null);
  const [activeTravelShift, setActiveTravelShift] = useState<ActiveTravelShift | null>(null);

  const setClockInSuccess = (id: string, time: string, office: string) => {
    setIsClockedIn(true);
    setAttendanceId(id);
    setClockInTime(time);
    setOfficeName(office);
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

  return (
    <AttendanceContext.Provider value={{
      isClockedIn,
      attendanceId,
      clockInTime,
      officeName,
      setClockInSuccess,
      setClockOutSuccess,
      activeTimer,
      startTaskTimer,
      stopTaskTimer,
      activeTravelShift,
      startTravelShift,
      endTravelShift,
    }}>
      {children}
    </AttendanceContext.Provider>
  );
};

export const useAttendance = () => useContext(AttendanceContext);
