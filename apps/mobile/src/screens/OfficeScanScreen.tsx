import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert, SafeAreaView } from 'react-native';
import { Camera, ArrowLeft, ShieldCheck, RefreshCw, CheckCircle, Smartphone } from 'lucide-react-native';
import { captureLocationWithAntiSpoof, captureNetworkDetails } from '../services/networkDetector';
import { getOrCreateDeviceBinding } from '../services/deviceSecurity';
import { runSelfieLivenessCheck } from '../services/livenessDetector';
import { useAttendance } from '../context/AttendanceContext';

interface OfficeScanProps {
  onBack: () => void;
}

export default function OfficeScanScreen({ onBack }: OfficeScanProps) {
  const { setClockInSuccess } = useAttendance();

  const [step, setStep] = useState<'scan_qr' | 'liveness' | 'verifying' | 'success'>('scan_qr');
  const [statusMessage, setStatusMessage] = useState('Point camera at laptop screen QR code');

  // Simulated QR scan trigger
  const handleSimulatedScan = async () => {
    // Transition to step 2: 1-second selfie liveness check
    setStep('liveness');
    setStatusMessage('Hold phone still: performing 1-second 3D liveness scan...');

    try {
      // Step 2: Facial Liveness & Embedding verification
      const livenessResult = await runSelfieLivenessCheck();
      if (!livenessResult.livenessPassed) {
        Alert.alert('Liveness Failed', '3D facial movement not detected. Please try again.');
        setStep('scan_qr');
        return;
      }

      setStep('verifying');
      setStatusMessage('Validating Wi-Fi BSSID, GPS, and device binding...');

      // Step 3: Location and Network Geofence
      const location = await captureLocationWithAntiSpoof();
      if (location.isMock) {
        Alert.alert('Spoof Detected', 'Mock location provider detected on device. Check-in rejected.');
        setStep('scan_qr');
        return;
      }

      const network = await captureNetworkDetails();
      const device = await getOrCreateDeviceBinding();

      // Final success
      await new Promise(resolve => setTimeout(resolve, 800));
      setStep('success');
      setStatusMessage('Physical Presence Verified! Clock-in confirmed.');

      setClockInSuccess(
        'att-uuid-' + Date.now(),
        new Date().toISOString(),
        'Corporate Office Terminal'
      );

      setTimeout(() => {
        onBack();
      }, 1500);
    } catch (err: any) {
      Alert.alert('Check-in Error', err.message || 'Verification failed');
      setStep('scan_qr');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <ArrowLeft size={22} color="#f8fafc" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>In-Office Verification</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={styles.content}>
        {/* Step Indicator */}
        <View style={styles.stepIndicatorRow}>
          <View style={[styles.stepBadge, step === 'scan_qr' ? styles.stepBadgeActive : styles.stepBadgeDone]}>
            <Text style={styles.stepBadgeText}>1. Dynamic QR</Text>
          </View>
          <View style={styles.stepDivider} />
          <View style={[styles.stepBadge, step === 'liveness' ? styles.stepBadgeActive : styles.stepBadgeDone]}>
            <Text style={styles.stepBadgeText}>2. Liveness</Text>
          </View>
          <View style={styles.stepDivider} />
          <View style={[styles.stepBadge, step === 'verifying' || step === 'success' ? styles.stepBadgeActive : styles.stepBadgeInactive]}>
            <Text style={styles.stepBadgeText}>3. Verify</Text>
          </View>
        </View>

        {/* Viewfinder Stage */}
        <View style={styles.viewfinderContainer}>
          {step === 'scan_qr' && (
            <View style={styles.qrTargetBox}>
              <View style={[styles.corner, styles.topLeft]} />
              <View style={[styles.corner, styles.topRight]} />
              <View style={[styles.corner, styles.bottomLeft]} />
              <View style={[styles.corner, styles.bottomRight]} />
              <Text style={styles.viewfinderInstructions}>
                Align the dynamic QR code displayed on the laptop kiosk inside this frame
              </Text>
            </View>
          )}

          {step === 'liveness' && (
            <View style={styles.faceOvalTarget}>
              <ActivityIndicator size="large" color="#3b82f6" />
              <Text style={styles.livenessText}>Keep face inside the oval</Text>
            </View>
          )}

          {step === 'verifying' && (
            <View style={styles.verifyingBox}>
              <ActivityIndicator size="large" color="#60a5fa" />
              <Text style={styles.verifyingTitle}>Verifying Zero-Trust Security</Text>
              <Text style={styles.verifyingSubtitle}>Checking Wi-Fi BSSID & single-use nonce</Text>
            </View>
          )}

          {step === 'success' && (
            <View style={styles.successBox}>
              <CheckCircle size={64} color="#22c55e" />
              <Text style={styles.successTitle}>Confirmed Present!</Text>
              <Text style={styles.successSubtitle}>Welcome to ZuiGO Office</Text>
            </View>
          )}
        </View>

        {/* Status Message */}
        <Text style={styles.statusDescription}>{statusMessage}</Text>

        {/* Action Button for Scanner */}
        {step === 'scan_qr' && (
          <TouchableOpacity style={styles.scanSimulateBtn} onPress={handleSimulatedScan}>
            <Camera size={20} color="#ffffff" />
            <Text style={styles.scanSimulateBtnText}>Simulate Camera Scan (Test Mode)</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  content: {
    flex: 1,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'space-between',
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
  stepIndicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 20,
  },
  stepBadge: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  stepBadgeActive: {
    backgroundColor: '#2563eb',
  },
  stepBadgeDone: {
    backgroundColor: 'rgba(34, 197, 94, 0.2)',
  },
  stepBadgeInactive: {
    backgroundColor: '#1e293b',
  },
  stepBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#ffffff',
  },
  stepDivider: {
    width: 16,
    height: 1,
    backgroundColor: '#334155',
    marginHorizontal: 4,
  },
  viewfinderContainer: {
    width: 300,
    height: 300,
    borderRadius: 24,
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  qrTargetBox: {
    width: 220,
    height: 220,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  corner: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: '#3b82f6',
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
  },
  viewfinderInstructions: {
    textAlign: 'center',
    fontSize: 12,
    color: '#94a3b8',
    lineHeight: 18,
  },
  faceOvalTarget: {
    width: 180,
    height: 240,
    borderRadius: 90,
    borderWidth: 3,
    borderColor: '#3b82f6',
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  livenessText: {
    fontSize: 12,
    color: '#93c5fd',
    fontWeight: '600',
  },
  verifyingBox: {
    alignItems: 'center',
    gap: 12,
  },
  verifyingTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ffffff',
  },
  verifyingSubtitle: {
    fontSize: 12,
    color: '#94a3b8',
  },
  successBox: {
    alignItems: 'center',
    gap: 12,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#4ade80',
  },
  successSubtitle: {
    fontSize: 13,
    color: '#cbd5e1',
  },
  statusDescription: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    marginVertical: 16,
  },
  scanSimulateBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 14,
    width: '100%',
    justifyContent: 'center',
  },
  scanSimulateBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
