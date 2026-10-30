import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, SafeAreaView, Alert } from 'react-native';
import { ArrowLeft, Play, Pause, Square, Lock, Clock, CheckCircle2, AlertTriangle } from 'lucide-react-native';
import { useAttendance } from '../context/AttendanceContext';

interface TaskItem {
  id: string;
  projectName: string;
  title: string;
  estimatedHours: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'TODO' | 'IN_PROGRESS' | 'DONE';
}

const SAMPLE_TASKS: TaskItem[] = [
  {
    id: 't-1',
    projectName: 'Mobile App V2',
    title: 'Implement On-Device Liveness Verification',
    estimatedHours: 4.0,
    priority: 'HIGH',
    status: 'IN_PROGRESS',
  },
  {
    id: 't-2',
    projectName: 'Client Field Visits',
    title: 'Visit Apollo City Hospital & Demo Kit',
    estimatedHours: 2.5,
    priority: 'HIGH',
    status: 'TODO',
  },
  {
    id: 't-3',
    projectName: 'Infrastructure',
    title: 'PostgreSQL PostGIS Geofence Optimization',
    estimatedHours: 3.0,
    priority: 'MEDIUM',
    status: 'TODO',
  },
];

export default function TaskStopwatchScreen({ onBack }: { onBack: () => void }) {
  const { isClockedIn, activeTimer, startTaskTimer, stopTaskTimer } = useAttendance();
  const [tasks] = useState<TaskItem[]>(SAMPLE_TASKS);
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

  const handleStartTask = (task: TaskItem) => {
    if (!isClockedIn) {
      Alert.alert(
        'Attendance Required',
        'Company policy requires you to be physically clocked in at the office or on verified field duty before tracking tasks.'
      );
      return;
    }

    startTaskTimer('entry-' + Date.now(), task.id, task.title);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <ArrowLeft size={22} color="#f8fafc" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Task Stopwatch</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={styles.content}>
        {/* Attendance Gating Warning Banner */}
        {!isClockedIn ? (
          <View style={styles.gatingWarningCard}>
            <View style={styles.warningIconRow}>
              <Lock size={22} color="#f87171" />
              <Text style={styles.gatingTitle}>Task Timers Locked</Text>
            </View>
            <Text style={styles.gatingDesc}>
              You cannot log active task hours while not clocked in. Please complete your in-office QR scan or field check-in first.
            </Text>
          </View>
        ) : (
          /* Live Stopwatch Banner */
          <View style={styles.stopwatchHero}>
            <Text style={styles.stopwatchLabel}>
              {activeTimer ? 'CURRENTLY LOGGING TIME' : 'STOPWATCH IDLE'}
            </Text>
            <Text style={styles.stopwatchTime}>{formatTimer(elapsedSeconds)}</Text>
            <Text style={styles.activeTaskName}>
              {activeTimer ? activeTimer.taskTitle : 'Select a task below to start stopwatch'}
            </Text>

            {activeTimer && (
              <TouchableOpacity style={styles.stopButton} onPress={stopTaskTimer}>
                <Square size={16} color="#ffffff" fill="#ffffff" />
                <Text style={styles.stopButtonText}>Stop & Log Time</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Assigned Task List */}
        <Text style={styles.taskListTitle}>Assigned Tasks Today</Text>

        <FlatList
          data={tasks}
          keyExtractor={item => item.id}
          renderItem={({ item }) => {
            const isThisRunning = activeTimer?.taskId === item.id;
            return (
              <View style={[styles.taskCard, isThisRunning && styles.taskCardRunning]}>
                <View style={styles.taskCardHeader}>
                  <Text style={styles.projectTag}>{item.projectName}</Text>
                  <View style={[styles.priorityBadge, item.priority === 'HIGH' ? styles.priorityHigh : styles.priorityMed]}>
                    <Text style={styles.priorityText}>{item.priority}</Text>
                  </View>
                </View>

                <Text style={styles.taskTitle}>{item.title}</Text>
                <Text style={styles.taskEst}>Est: {item.estimatedHours} hrs</Text>

                <TouchableOpacity
                  style={[
                    styles.taskActionButton,
                    isThisRunning ? styles.runningButton : styles.startButton,
                    !isClockedIn && styles.disabledButton,
                  ]}
                  onPress={() => (isThisRunning ? stopTaskTimer() : handleStartTask(item))}
                  disabled={!isClockedIn}
                >
                  {isThisRunning ? (
                    <>
                      <Pause size={16} color="#ffffff" />
                      <Text style={styles.actionButtonText}>Pause Timer</Text>
                    </>
                  ) : (
                    <>
                      <Play size={16} color="#ffffff" fill="#ffffff" />
                      <Text style={styles.actionButtonText}>Start Task</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            );
          }}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
  },
  backButton: {
    padding: 8,
    borderRadius: 10,
    backgroundColor: '#1e293b',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ffffff',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  gatingWarningCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
  },
  warningIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  gatingTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f87171',
  },
  gatingDesc: {
    fontSize: 13,
    color: '#fca5a5',
    lineHeight: 18,
  },
  stopwatchHero: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: '#3b82f6',
    alignItems: 'center',
    marginBottom: 20,
  },
  stopwatchLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: '#93c5fd',
    letterSpacing: 1,
    marginBottom: 6,
  },
  stopwatchTime: {
    fontFamily: 'JetBrains Mono, monospace',
    fontSize: 40,
    fontWeight: '900',
    color: '#ffffff',
    marginVertical: 4,
  },
  activeTaskName: {
    fontSize: 14,
    color: '#cbd5e1',
    textAlign: 'center',
    marginBottom: 16,
  },
  stopButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#dc2626',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  stopButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  taskListTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 12,
  },
  taskCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
    marginBottom: 12,
  },
  taskCardRunning: {
    borderColor: '#3b82f6',
    backgroundColor: 'rgba(30, 58, 138, 0.25)',
  },
  taskCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  projectTag: {
    fontSize: 12,
    fontWeight: '700',
    color: '#60a5fa',
  },
  priorityBadge: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  priorityHigh: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  priorityMed: {
    backgroundColor: 'rgba(234, 179, 8, 0.2)',
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#ffffff',
  },
  taskTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 6,
  },
  taskEst: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 12,
  },
  taskActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
    borderRadius: 10,
  },
  startButton: {
    backgroundColor: '#2563eb',
  },
  runningButton: {
    backgroundColor: '#eab308',
  },
  disabledButton: {
    backgroundColor: '#334155',
    opacity: 0.5,
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
});
