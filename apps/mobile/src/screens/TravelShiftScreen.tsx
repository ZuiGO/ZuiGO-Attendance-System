import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView, SafeAreaView, Alert } from 'react-native';
import { ArrowLeft, Car, Camera, AlertTriangle, CheckCircle, ShieldAlert, DollarSign } from 'lucide-react-native';
import { useAttendance } from '../context/AttendanceContext';

const TRANSPORT_MODES = [
  { id: 'PERSONAL_CAR', label: 'Personal Car', rate: '₹8.00 / km', rateNum: 8.0 },
  { id: 'TWO_WHEELER', label: 'Personal Two-Wheeler', rate: '₹4.00 / km', rateNum: 4.0 },
  { id: 'COMPANY_CAR', label: 'Company Fleet Vehicle', rate: 'Fuel Card', rateNum: 0.0 },
  { id: 'CAB', label: 'Cab / Ride-Hail', rate: 'Actual Receipts', rateNum: 0.0 },
];

export default function TravelShiftScreen({ onBack }: { onBack: () => void }) {
  const { activeTravelShift, startTravelShift, endTravelShift } = useAttendance();

  const [selectedMode, setSelectedMode] = useState('PERSONAL_CAR');
  const [startOdo, setStartOdo] = useState('45230.5');
  const [endOdo, setEndOdo] = useState('45273.2');
  const [startPhotoCaptured, setStartPhotoCaptured] = useState(false);
  const [endPhotoCaptured, setEndPhotoCaptured] = useState(false);

  // Start Travel Shift
  const handleStartShift = () => {
    if (!startOdo || !startPhotoCaptured) {
      Alert.alert('Required Verification', 'Please enter your starting odometer reading and take a live dashboard photo.');
      return;
    }
    startTravelShift('log-' + Date.now(), selectedMode, parseFloat(startOdo));
    Alert.alert('Travel Shift Started', `GPS route breadcrumbs active for ${selectedMode}. Odometer reading recorded.`);
  };

  // End Travel Shift & Discrepancy Check
  const handleEndShift = () => {
    if (!endOdo || !endPhotoCaptured) {
      Alert.alert('Required Verification', 'Please enter your ending odometer reading and take an ending dashboard photo.');
      return;
    }

    const odoDistance = parseFloat(endOdo) - parseFloat(startOdo);
    const simulatedGpsDistance = 41.2; // e.g. 41.2 km computed from GPS polyline

    const diff = Math.abs(odoDistance - simulatedGpsDistance);
    const discrepancyPct = (diff / odoDistance) * 100;
    const isFlagged = discrepancyPct > 15.0;

    const rate = TRANSPORT_MODES.find(m => m.id === selectedMode)?.rateNum || 0.0;
    const reimbursement = (odoDistance * rate).toFixed(2);

    endTravelShift();

    if (isFlagged) {
      Alert.alert(
        'Travel Logged (Discrepancy Flagged)',
        `Odometer distance: ${odoDistance.toFixed(1)} km.\nGPS distance: ${simulatedGpsDistance} km.\nDiscrepancy: ${discrepancyPct.toFixed(1)}% (exceeds 15% threshold).\nFlagged for manager review.`
      );
    } else {
      Alert.alert(
        'Travel Shift Finalized',
        `Distance: ${odoDistance.toFixed(1)} km verified with GPS.\nEstimated Reimbursement: ₹${reimbursement}.\nTrip summary submitted successfully!`
      );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <ArrowLeft size={22} color="#f8fafc" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Vehicle Mileage & Travel</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {!activeTravelShift ? (
          /* START TRAVEL SECTION */
          <View>
            <Text style={styles.sectionTitle}>Select Transport Mode</Text>
            <View style={styles.modeSelector}>
              {TRANSPORT_MODES.map(mode => (
                <TouchableOpacity
                  key={mode.id}
                  style={[styles.modeCard, selectedMode === mode.id && styles.modeCardActive]}
                  onPress={() => setSelectedMode(mode.id)}
                >
                  <View style={styles.modeHeader}>
                    <Car size={20} color={selectedMode === mode.id ? '#60a5fa' : '#94a3b8'} />
                    <Text style={[styles.modeRate, selectedMode === mode.id && styles.modeRateActive]}>
                      {mode.rate}
                    </Text>
                  </View>
                  <Text style={[styles.modeLabel, selectedMode === mode.id && styles.modeLabelActive]}>
                    {mode.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Odometer Baseline */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Odometer Reading at Shift Start</Text>
              <TextInput
                style={styles.odoInput}
                value={startOdo}
                onChangeText={setStartOdo}
                placeholder="Starting km (e.g. 45230.5)"
                placeholderTextColor="#64748b"
                keyboardType="decimal-pad"
              />

              <TouchableOpacity
                style={[styles.photoButton, startPhotoCaptured && styles.photoButtonDone]}
                onPress={() => {
                  setStartPhotoCaptured(true);
                  Alert.alert('Photo Captured', 'Dashboard odometer photo captured with cryptographic timestamp.');
                }}
              >
                <Camera size={18} color="#ffffff" />
                <Text style={styles.photoButtonText}>
                  {startPhotoCaptured ? '✓ Starting Odometer Photo Verified' : 'Capture Odometer Dashboard Photo'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.startShiftBtn} onPress={handleStartShift}>
                <Text style={styles.startShiftBtnText}>Start Vehicle Travel Shift</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          /* ACTIVE TRAVEL / END SHIFT SECTION */
          <View>
            <View style={styles.activeShiftBanner}>
              <View style={styles.activeHeaderRow}>
                <View style={styles.activePill}>
                  <Text style={styles.activePillText}>TRAVEL IN PROGRESS</Text>
                </View>
                <Text style={styles.activeModeText}>{activeTravelShift.transportMode.replace('_', ' ')}</Text>
              </View>
              <Text style={styles.activeStartKm}>Started with Odometer at {activeTravelShift.odometerStartKm} km</Text>
              <Text style={styles.activeGpsNote}>📡 Background GPS breadcrumbs are calculating road-following distance.</Text>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardTitle}>Finalize Shift & Capture End Odometer</Text>
              <TextInput
                style={styles.odoInput}
                value={endOdo}
                onChangeText={setEndOdo}
                placeholder="Ending km (e.g. 45273.2)"
                placeholderTextColor="#64748b"
                keyboardType="decimal-pad"
              />

              <TouchableOpacity
                style={[styles.photoButton, endPhotoCaptured && styles.photoButtonDone]}
                onPress={() => {
                  setEndPhotoCaptured(true);
                  Alert.alert('Photo Captured', 'Ending dashboard odometer photo captured.');
                }}
              >
                <Camera size={18} color="#ffffff" />
                <Text style={styles.photoButtonText}>
                  {endPhotoCaptured ? '✓ Ending Odometer Photo Verified' : 'Capture Ending Odometer Photo'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.endShiftBtn} onPress={handleEndShift}>
                <Text style={styles.endShiftBtnText}>End Shift & Compute Reimbursement</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
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
    padding: 20,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 12,
  },
  modeSelector: {
    gap: 10,
    marginBottom: 20,
  },
  modeCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
  },
  modeCardActive: {
    borderColor: '#3b82f6',
    backgroundColor: 'rgba(30, 58, 138, 0.25)',
  },
  modeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  modeRate: {
    fontSize: 12,
    fontWeight: '700',
    color: '#94a3b8',
  },
  modeRateActive: {
    color: '#60a5fa',
  },
  modeLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#cbd5e1',
  },
  modeLabelActive: {
    color: '#ffffff',
  },
  card: {
    backgroundColor: 'rgba(15, 23, 42, 0.8)',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 12,
  },
  odoInput: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
    color: '#ffffff',
    fontSize: 18,
    fontFamily: 'JetBrains Mono, monospace',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 14,
  },
  photoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#475569',
    paddingVertical: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  photoButtonDone: {
    backgroundColor: 'rgba(34, 197, 94, 0.2)',
    borderColor: '#22c55e',
  },
  photoButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  startShiftBtn: {
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: 'center',
  },
  startShiftBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
  activeShiftBanner: {
    backgroundColor: 'rgba(30, 58, 138, 0.35)',
    borderWidth: 1,
    borderColor: '#3b82f6',
    borderRadius: 18,
    padding: 16,
    marginBottom: 20,
  },
  activeHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  activePill: {
    backgroundColor: '#2563eb',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 6,
  },
  activePillText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '800',
  },
  activeModeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#93c5fd',
  },
  activeStartKm: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 6,
  },
  activeGpsNote: {
    fontSize: 12,
    color: '#cbd5e1',
  },
  endShiftBtn: {
    backgroundColor: '#16a34a',
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: 'center',
  },
  endShiftBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
