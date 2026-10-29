import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'elimuquest.access-token';

export const authTokenStorage = {
  get: () => Platform.OS === 'web' ? AsyncStorage.getItem(TOKEN_KEY) : SecureStore.getItemAsync(TOKEN_KEY),
  set: (token: string) => Platform.OS === 'web'
    ? AsyncStorage.setItem(TOKEN_KEY, token)
    : SecureStore.setItemAsync(TOKEN_KEY, token),
  remove: () => Platform.OS === 'web' ? AsyncStorage.removeItem(TOKEN_KEY) : SecureStore.deleteItemAsync(TOKEN_KEY),
};
