import { Redirect } from 'expo-router';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useAuthStore } from '../src/stores/authStore';
import { useAuthStatus } from '../src/providers/AuthProvider';
import { colors, spacing } from '../src/theme';

export default function Index() {
  const hydrated = useAuthStore((state) => state.hydrated);
  const user = useAuthStore((state) => state.user);
  const { restoreError, retryRestore } = useAuthStatus();

  if (!hydrated) {
    return <View style={styles.container}><ActivityIndicator color={colors.primary} /></View>;
  }
  if (restoreError) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>{restoreError}</Text>
        <Pressable onPress={() => void retryRestore()} accessibilityRole="button">
          <Text style={styles.retry}>Try again</Text>
        </Pressable>
      </View>
    );
  }
  return <Redirect href={user ? '/(tabs)' : '/(auth)/welcome'} />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    backgroundColor: colors.canvas,
  },
  error: { color: colors.textSoft, textAlign: 'center', marginBottom: spacing.md },
  retry: { color: colors.primary, fontWeight: '700' },
});
