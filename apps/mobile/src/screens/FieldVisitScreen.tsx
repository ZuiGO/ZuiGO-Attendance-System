import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, SafeAreaView, Alert, Modal, TextInput, ActivityIndicator } from 'react-native';
import { ArrowLeft, MapPin, Clock, ShieldCheck, CheckCircle2, MessageSquare, Camera, AlertCircle } from 'lucide-react-native';

interface FieldStop {
  id: string;
  name: string;
  clientType: string;
  contactPerson: string;
  contactPhone: string;
  minDwellMinutes: number;
  status: 'PENDING' | 'ARRIVED' | 'COMPLETED';
  arrivalTime?: Date;
}

const INITIAL_STOPS: FieldStop[] = [
  {
    id: 's-1',
    name: 'Apollo City Hospital',
    clientType: 'HOSPITAL',
    contactPerson: 'Dr. Sharma (Medical Superintendent)',
    contactPhone: '+919876543210',
    minDwellMinutes: 30,
    status: 'PENDING',
  },
  {
    id: 's-2',
    name: 'Metro Pharma Distributor',
    clientType: 'DISTRIBUTOR',
    contactPerson: 'Mr. Rajesh Gupta',
    contactPhone: '+919812345678',
    minDwellMinutes: 30,
    status: 'PENDING',
  },
  {
    id: 's-3',
    name: 'LifeCare Diagnostics',
    clientType: 'DEALER',
    contactPerson: 'Dr. Neha Verma',
    contactPhone: '+919898765432',
    minDwellMinutes: 30,
    status: 'PENDING',
  },
];

export default function FieldVisitScreen({ onBack }: { onBack: () => void }) {
  const [stops, setStops] = useState<FieldStop[]>(INITIAL_STOPS);
  const [selectedStop, setSelectedStop] = useState<FieldStop | null>(null);

  // Dwell timer state
  const [dwellElapsedSeconds, setDwellElapsedSeconds] = useState(0);

  // OTP Modal State
  const [isOtpModalVisible, setIsOtpModalVisible] = useState(false);
  const [enteredOtp, setEnteredOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpLoading, setOtpLoading] = useState(false);

  // Live Dwell Timer Tick
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    const activeArrivedStop = stops.find(s => s.status === 'ARRIVED');
    if (activeArrivedStop && activeArrivedStop.arrivalTime) {
      interval = setInterval(() => {
        const sec = Math.floor((Date.now() - activeArrivedStop.arrivalTime!.getTime()) / 1000);
        setDwellElapsedSeconds(sec);
      }, 1000);
    } else {
      setDwellElapsedSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [stops]);

  const activeArrivedStop = stops.find(s => s.status === 'ARRIVED');
  const requiredDwellSeconds = (activeArrivedStop?.minDwellMinutes || 30) * 60;
  const isDwellSatisfied = dwellElapsedSeconds >= requiredDwellSeconds;
  const dwellPercentage = Math.min((dwellElapsedSeconds / requiredDwellSeconds) * 100, 100);

  // 1. Arrive at Destination
  const handleArrive = (stop: FieldStop) => {
    Alert.alert(
      'Verify Arrival',
      `Validating physical proximity (< 75m) to ${stop.name}...`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm GPS Arrival',
          onPress: () => {
            const now = new Date();
            setStops(prev =>
              prev.map(s => (s.id === stop.id ? { ...s, status: 'ARRIVED', arrivalTime: now } : s))
            );
            Alert.alert('Arrival Confirmed', `You are inside ${stop.name} geofence. The 30-minute dwell timer has started.`);
          },
        },
      ]
    );
  };

  // 2. Open OTP Modal to finalize visit
  const handleOpenFinalize = (stop: FieldStop) => {
    if (!isDwellSatisfied) {
      const remainingMins = Math.ceil((requiredDwellSeconds - dwellElapsedSeconds) / 60);
      Alert.alert(
        'Dwell Time Not Met',
        `Anti-drive-by policy requires at least 30 minutes at client site. Please stay an additional ${remainingMins} minutes before completing the visit.`
      );
      return;
    }
    setSelectedStop(stop);
    setIsOtpModalVisible(true);
    setOtpSent(false);
    setEnteredOtp('');
  };

  // 3. Request Client SMS/WhatsApp OTP
  const handleRequestOtp = () => {
    setOtpLoading(true);
    setTimeout(() => {
      setOtpLoading(false);
      setOtpSent(true);
      Alert.alert('OTP Dispatched', 'A 4-digit verification code has been sent via SMS/WhatsApp to the client contact.');
    }, 1000);
  };

  // 4. Verify OTP & Capture Watermarked Photo
  const handleVerifyOtpAndComplete = () => {
    if (enteredOtp !== '4921' && enteredOtp.length !== 4) {
      Alert.alert('Invalid Code', 'Please enter a valid 4-digit OTP provided by the client.');
      return;
    }

    setIsOtpModalVisible(false);
    setStops(prev =>
      prev.map(s => (s.id === selectedStop?.id ? { ...s, status: 'COMPLETED' } : s))
    );
    Alert.alert(
      'Visit Verified & Completed',
      'Client OTP validated. Watermarked photo proof captured and submitted to management.'
    );
  };

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}m ${s.toString().padStart(2, '0')}s`;
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <ArrowLeft size={22} color="#f8fafc" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Field Visit Mode</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={styles.content}>
        {/* Active Dwell Timer Bar (If Arrived) */}
        {activeArrivedStop && (
          <View style={styles.dwellBanner}>
            <View style={styles.dwellHeader}>
              <View style={styles.dwellBadge}>
                <Clock size={16} color="#60a5fa" />
                <Text style={styles.dwellBadgeText}>DWELL TIMER ACTIVE</Text>
              </View>
              <Text style={styles.dwellTimeTicker}>{formatSeconds(dwellElapsedSeconds)} / 30m</Text>
            </View>

            <Text style={styles.activeStopName}>At: {activeArrivedStop.name}</Text>

            {/* Progress Bar */}
            <View style={styles.progressBarTrack}>
              <View style={[styles.progressBarFill, { width: `${dwellPercentage}%`, backgroundColor: isDwellSatisfied ? '#22c55e' : '#3b82f6' }]} />
            </View>

            <Text style={styles.dwellNoticeText}>
              {isDwellSatisfied
                ? '✅ 30-minute dwell time satisfied! You can now complete the visit.'
                : `⏳ Anti-Drive-By Protection: Stay at destination for 30 minutes.`}
            </Text>
          </View>
        )}

        {/* Assigned Route Stops Header */}
        <Text style={styles.sectionTitle}>Today's Assigned Route ({stops.filter(s => s.status === 'COMPLETED').length}/{stops.length} Visited)</Text>

        <FlatList
          data={stops}
          keyExtractor={item => item.id}
          renderItem={({ item, index }) => (
            <View style={[styles.stopCard, item.status === 'COMPLETED' && styles.stopCardDone]}>
              <View style={styles.stopCardHeader}>
                <View style={styles.stopNumberBadge}>
                  <Text style={styles.stopNumberText}>{index + 1}</Text>
                </View>
                <View style={{ flex: 1, marginLeft: 10 }}>
                  <Text style={styles.stopTitle}>{item.name}</Text>
                  <Text style={styles.stopType}>{item.clientType} • 30m Min Dwell</Text>
                </View>
                {item.status === 'COMPLETED' && <CheckCircle2 size={24} color="#22c55e" />}
              </View>

              <Text style={styles.contactInfo}>👤 {item.contactPerson}</Text>
              <Text style={styles.contactPhone}>📞 {item.contactPhone}</Text>

              {item.status === 'PENDING' && (
                <TouchableOpacity style={styles.arriveBtn} onPress={() => handleArrive(item)}>
                  <MapPin size={16} color="#ffffff" />
                  <Text style={styles.arriveBtnText}>Arrive & Start Dwell Timer</Text>
                </TouchableOpacity>
              )}

              {item.status === 'ARRIVED' && (
                <TouchableOpacity
                  style={[styles.completeBtn, !isDwellSatisfied && styles.disabledCompleteBtn]}
                  onPress={() => handleOpenFinalize(item)}
                >
                  <ShieldCheck size={16} color="#ffffff" />
                  <Text style={styles.completeBtnText}>
                    {isDwellSatisfied ? 'Verify Client OTP & Complete' : `Wait ${Math.ceil((requiredDwellSeconds - dwellElapsedSeconds) / 60)}m to Complete`}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        />
      </View>

      {/* Client OTP Verification Modal */}
      <Modal visible={isOtpModalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <MessageSquare size={24} color="#3b82f6" />
              <Text style={styles.modalTitle}>Client Counter-Verification</Text>
            </View>

            <Text style={styles.modalDesc}>
              Ask {selectedStop?.contactPerson} for the 4-digit code sent to their phone to verify this meeting.
            </Text>

            {!otpSent ? (
              <TouchableOpacity style={styles.sendOtpBtn} onPress={handleRequestOtp} disabled={otpLoading}>
                {otpLoading ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <Text style={styles.sendOtpBtnText}>Send OTP to {selectedStop?.contactPhone.substring(0, 7)}***</Text>
                )}
              </TouchableOpacity>
            ) : (
              <View style={{ width: '100%', gap: 14 }}>
                <TextInput
                  style={styles.otpInput}
                  value={enteredOtp}
                  onChangeText={setEnteredOtp}
                  placeholder="Enter 4-digit code (e.g. 4921)"
                  placeholderTextColor="#64748b"
                  keyboardType="number-pad"
                  maxLength={4}
                />

                <TouchableOpacity style={styles.verifyOtpBtn} onPress={handleVerifyOtpAndComplete}>
                  <Camera size={18} color="#ffffff" />
                  <Text style={styles.verifyOtpBtnText}>Capture Photo & Confirm Visit</Text>
                </TouchableOpacity>
              </View>
            )}

            <TouchableOpacity style={styles.cancelModalBtn} onPress={() => setIsOtpModalVisible(false)}>
              <Text style={styles.cancelModalBtnText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
  dwellBanner: {
    backgroundColor: 'rgba(30, 58, 138, 0.35)',
    borderWidth: 1,
    borderColor: '#3b82f6',
    borderRadius: 18,
    padding: 16,
    marginBottom: 20,
  },
  dwellHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  dwellBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dwellBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#93c5fd',
    letterSpacing: 0.5,
  },
  dwellTimeTicker: {
    fontFamily: 'JetBrains Mono, monospace',
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  activeStopName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 10,
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  dwellNoticeText: {
    fontSize: 12,
    color: '#cbd5e1',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 12,
  },
  stopCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
    marginBottom: 14,
  },
  stopCardDone: {
    backgroundColor: 'rgba(22, 101, 52, 0.15)',
    borderColor: 'rgba(34, 197, 94, 0.2)',
  },
  stopCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  stopNumberBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#1e293b',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stopNumberText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#93c5fd',
  },
  stopTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
  },
  stopType: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  contactInfo: {
    fontSize: 13,
    color: '#cbd5e1',
    marginTop: 4,
  },
  contactPhone: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
    marginBottom: 12,
  },
  arriveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    borderRadius: 10,
  },
  arriveBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  completeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#16a34a',
    paddingVertical: 10,
    borderRadius: 10,
  },
  disabledCompleteBtn: {
    backgroundColor: '#334155',
    opacity: 0.6,
  },
  completeBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#0f172a',
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#f8fafc',
  },
  modalDesc: {
    fontSize: 13,
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18,
  },
  sendOtpBtn: {
    backgroundColor: '#2563eb',
    width: '100%',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  sendOtpBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  otpInput: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3b82f6',
    color: '#ffffff',
    fontSize: 18,
    fontFamily: 'JetBrains Mono, monospace',
    textAlign: 'center',
    paddingVertical: 12,
  },
  verifyOtpBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#16a34a',
    paddingVertical: 12,
    borderRadius: 12,
  },
  verifyOtpBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  cancelModalBtn: {
    marginTop: 16,
    paddingVertical: 6,
  },
  cancelModalBtnText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '600',
  },
});
