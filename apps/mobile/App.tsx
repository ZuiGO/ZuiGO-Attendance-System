import React, { useState } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { AttendanceProvider } from './src/context/AttendanceContext';
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import OfficeScanScreen from './src/screens/OfficeScanScreen';
import TaskStopwatchScreen from './src/screens/TaskStopwatchScreen';
import FieldVisitScreen from './src/screens/FieldVisitScreen';
import TravelShiftScreen from './src/screens/TravelShiftScreen';

type ScreenName = 'dashboard' | 'office_scan' | 'tasks' | 'field_visit' | 'travel';

function RootNavigator() {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('dashboard');

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  switch (currentScreen) {
    case 'office_scan':
      return <OfficeScanScreen onBack={() => setCurrentScreen('dashboard')} />;
    case 'tasks':
      return <TaskStopwatchScreen onBack={() => setCurrentScreen('dashboard')} />;
    case 'field_visit':
      return <FieldVisitScreen onBack={() => setCurrentScreen('dashboard')} />;
    case 'travel':
      return <TravelShiftScreen onBack={() => setCurrentScreen('dashboard')} />;
    case 'dashboard':
    default:
      return <DashboardScreen onNavigate={screen => setCurrentScreen(screen)} />;
  }
}

export default function App() {
  return (
    <AuthProvider>
      <AttendanceProvider>
        <StatusBar style="light" />
        <RootNavigator />
      </AttendanceProvider>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#090d16',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
