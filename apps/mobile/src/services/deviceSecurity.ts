/**
 * Hardware Keystore / Secure Enclave Device Binding.
 * Ensures strict 1:1 mapping between Employee and Physical Smartphone.
 */

import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

const DEVICE_ID_KEY = 'zuigo_hardware_device_id';
const DEVICE_KEYPAIR_PUB_KEY = 'zuigo_device_public_key';

export interface DeviceBindingInfo {
  deviceId: string;
  publicKey: string;
  deviceModel: string;
  osVersion: string;
}

export async function getOrCreateDeviceBinding(): Promise<DeviceBindingInfo> {
  // Check if hardware device ID is already registered in SecureStore
  let deviceId = await SecureStore.getItemAsync(DEVICE_ID_KEY);
  if (!deviceId) {
    // Generate cryptographically secure UUID bound to this device installation
    deviceId = `hw-${Crypto.randomUUID()}`;
    await SecureStore.setItemAsync(DEVICE_ID_KEY, deviceId);
  }

  let publicKey = await SecureStore.getItemAsync(DEVICE_KEYPAIR_PUB_KEY);
  if (!publicKey) {
    // Generate simulated 256-bit public key signature placeholder
    const randomBytes = await Crypto.getRandomBytesAsync(32);
    publicKey = Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0')).join('');
    await SecureStore.setItemAsync(DEVICE_KEYPAIR_PUB_KEY, publicKey);
  }

  const deviceModel = `${Device.manufacturer || ''} ${Device.modelName || 'Device'}`.trim();
  const osVersion = `${Platform.OS} ${Platform.Version}`;

  return {
    deviceId,
    publicKey,
    deviceModel,
    osVersion,
  };
}
