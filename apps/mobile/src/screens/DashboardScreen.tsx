import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Alert } from 'react-native';
import { ShieldCheck, LogOut, QrCode, Play, Pause, Square, MapPin, Car, Clock, CheckCircle2 } from 'lucide-react-native';
import { useAuth } from '../context/AuthContext';
import { useAttendance } from '../context/AttendanceContext';

interface DashboardProps {
  onNavigate: (screen: 'dashboard' | 'office_scan' | 'tasks' | 'field_visit' | 'travel') => void;
}

export default function DashboardScreen({ onNavigate }: DashboardProps) {
  const { user, logout } = useAuth();
  const { isClockedIn, clockInTime, officeName, setClockOutSuccess, activeTimer, stopTaskTimer, activeTravelShift } = useAttendance();

  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (activeTimer) {
      interval = setInterval(() => {
        const diff = Math.floor((Date.now() - activeTimer.startTime.getTime()) / 1000);
        setElapsedSeconds(diff);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeTimer]);

  const formatTimer = (sec: number) => {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleClockOut = () => {
    Alert.alert(
      'Clock Out',
      'Are you sure you want to clock out for the day? Any active task timer will be automatically stopped.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm Clock Out',
          style: 'destructive',
          onPress: () => {
            setClockOutSuccess();
            Alert.alert('Clocked Out', 'Your attendance session has been finalized.');
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Top Header */}
        <View style={styles.topHeader}>
          <View>
            <Text style={styles.welcomeText}>Hello, {user?.name || 'Employee'}</Text>
            <Text style={styles.roleText}>{user?.role || 'Staff'} • {user?.email}</Text>
          </View>
          <TouchableOpacity onPress={logout} style={styles.logoutButton}>
            <LogOut size={20} color="#94a3b8" />
          </TouchableOpacity>
        </View>

        {/* Hero Attendance Status Card */}
        <View style={[styles.statusCard, isClockedIn ? styles.statusCardPresent : styles.statusCardAbsent]}>
          <View style={styles.statusHeader}>
            <View style={styles.statusBadge}>
              <View style={[styles.statusDot, { backgroundColor: isClockedIn ? '#22c55e' : '#eab308' }]} />
              <Text style={[styles.statusBadgeText, { color: isClockedIn ? '#4ade80' : '#fde047' }]}>
                {isClockedIn ? 'OFFICE ATTENDANCE: PRESENT' : 'NOT CLOCKED IN'}
              </Text>
            </View>
            <ShieldCheck size={20} color={isClockedIn ? '#4ade80' : '#94a3b8'} />
          </View>

          {isClockedIn ? (
            <View style={styles.statusBody}>
              <Text style={styles.officeNameText}>📍 {officeName || 'Corporate Office'}</Text>
              <Text style={styles.clockInTimeText}>Clocked In: {clockInTime ? new Date(clockInTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '09:02 AM'}</Text>
              <TouchableOpacity style={styles.clockOutBtn} onPress={handleClockOut}>
                <Text style={styles.clockOutBtnText}>Clock Out for the Day</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.statusBody}>
              <Text style={styles.absentNoticeText}>
                You are currently outside or have not verified your in-office attendance yet.
              </Text>
              <TouchableOpacity style={styles.clockInActionBtn} onPress={() => onNavigate('office_scan')}>
                <QrCode size={18} color="#ffffff" />
                <Text style={styles.clockInActionBtnText}>Scan In-Office Dynamic QR</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Active Task Stopwatch Widget (If running) */}
        {activeTimer && (
          <View style={styles.activeTimerWidget}>
            <View style={styles.activeTimerHeader}>
              <View style={styles.timerIndicatorRow}>
                <View style={styles.pulsingRedDot} />
                <Text style={styles.timerSubtitle}>ACTIVE TASK TRACKER</Text>
              </View>
              <Text style={styles.timerTickerText}>{formatTimer(elapsedSeconds)}</Text>
            </View>
            <Text style={styles.activeTaskTitleText}>{activeTimer.taskTitle}</Text>
            <TouchableOpacity style={styles.stopTimerSmallBtn} onPress={stopTaskTimer}>
              <Square size={14} color="#ffffff" fill="#ffffff" />
              <Text style={styles.stopTimerSmallBtnText}>Stop Stopwatch</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Active Travel Shift Widget (If running) */}
        {activeTravelShift && (
          <View style={styles.activeTravelWidget}>
            <View style={styles.activeTimerHeader}>
              <Car size={18} color="#60a5fa" />
              <Text style={styles.travelModeTitle}>{activeTravelShift.transportMode.replace('_', ' ')} IN PROGRESS</Text>
            </View>
            <Text style={styles.travelStartOdo}>Started at {activeTravelShift.odometerStartKm || 0} km</Text>
          </View>
        )}

        {/* Main Modules Grid */}
        <Text style={styles.sectionTitle}>Work & Tracking Modules</Text>

        <View style={styles.modulesGrid}>
          {/* Module 1: In-Office QR Check-In */}
          <TouchableOpacity style={styles.moduleCard} onPress={() => onNavigate('office_scan')}>
            <View style={[styles.moduleIconBox, { backgroundColor: 'rgba(59, 130, 246, 0.15)' }]}>
              <QrCode size={26} color="#60a5fa" />
            </View>
            <Text style={styles.moduleTitle}>Office Attendance</Text>
            <Text style={styles.moduleDesc}>Dynamic 15s QR + 1-Sec Face Liveness</Text>
          </TouchableOpacity>

          {/* Module 2: Task Stopwatch */}
          <TouchableOpacity style={styles.moduleCard} onPress={() => onNavigate('tasks')}>
            <View style={[styles.moduleIconBox, { backgroundColor: 'rgba(168, 85, 247, 0.15)' }]}>
              <Clock size={26} color="#c084fc" />
            </View>
            <Text style={styles.moduleTitle}>Task Stopwatch</Text>
            <Text style={styles.moduleDesc}>Attendance-gated project task timer</Text>
          </TouchableOpacity>

          {/* Module 3: Field Visit Mode */}
          <TouchableOpacity style={styles.moduleCard} onPress={() => onNavigate('field_visit')}>
            <View style={[styles.moduleIconBox, { backgroundColor: 'rgba(34, 197, 94, 0.15)' }]}>
              <MapPin size={26} color="#4ade80" />
            </View>
            <Text style={styles.moduleTitle}>Field Visit Mode</Text>
            <Text style={styles.moduleDesc}>30-Min Dwell + Client SMS/WA OTP</Text>
          </TouchableOpacity>

          {/* Module 4: Vehicle Travel Shift */}
          <TouchableOpacity style={styles.moduleCard} onPress={() => onNavigate('travel')}>
            <View style={[styles.moduleIconBox, { backgroundColor: 'rgba(249, 115, 22, 0.15)' }]}>
              <Car size={26} color="#fb923c" />
            </View>
            <Text style={styles.moduleTitle}>Vehicle Mileage</Text>
            <Text style={styles.moduleDesc}>Odometer photo & route audit</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  scrollContent: {
    padding: 20,
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  welcomeText: {
    fontSize: 22,
    fontWeight: '800',
    color: '#ffffff',
  },
  roleText: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 2,
  },
  logoutButton: {
    padding: 10,
    backgroundColor: '#1e293b',
    borderRadius: 12,
  },
  statusCard: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    marginBottom: 20,
  },
  statusCardPresent: {
    backgroundColor: 'rgba(22, 101, 52, 0.25)',
    borderColor: 'rgba(34, 197, 94, 0.3)',
  },
  statusCardAbsent: {
    backgroundColor: 'rgba(30, 41, 59, 0.7)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  statusBody: {
    gap: 6,
  },
  officeNameText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  clockInTimeText: {
    fontSize: 13,
    color: '#86efac',
  },
  clockOutBtn: {
    marginTop: 12,
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderWidth: 1,
    borderColor: '#ef4444',
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  clockOutBtnText: {
    color: '#fca5a5',
    fontWeight: '700',
    fontSize: 13,
  },
  absentNoticeText: {
    fontSize: 13,
    color: '#94a3b8',
    lineHeight: 18,
  },
  clockInActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    borderRadius: 12,
    marginTop: 12,
  },
  clockInActionBtnText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 14,
  },
  activeTimerWidget: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderWidth: 1,
    borderColor: '#3b82f6',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
  },
  activeTimerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  timerIndicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pulsingRedDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ef4444',
  },
  timerSubtitle: {
    fontSize: 11,
    fontWeight: '800',
    color: '#93c5fd',
    letterSpacing: 0.5,
  },
  timerTickerText: {
    fontFamily: 'JetBrains Mono, monospace',
    fontSize: 18,
    fontWeight: '800',
    color: '#ffffff',
  },
  activeTaskTitleText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#cbd5e1',
    marginBottom: 10,
  },
  stopTimerSmallBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#dc2626',
    paddingVertical: 8,
    borderRadius: 8,
  },
  stopTimerSmallBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  activeTravelWidget: {
    backgroundColor: 'rgba(30, 58, 138, 0.3)',
    borderWidth: 1,
    borderColor: '#3b82f6',
    borderRadius: 16,
    padding: 14,
    marginBottom: 20,
  },
  travelModeTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#93c5fd',
  },
  travelStartOdo: {
    fontSize: 12,
    color: '#cbd5e1',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 14,
  },
  modulesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 14,
  },
  moduleCard: {
    width: '47.5%',
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
  },
  moduleIconBox: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  moduleTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 4,
  },
  moduleDesc: {
    fontSize: 12,
    color: '#94a3b8',
    lineHeight: 16,
  },
});
