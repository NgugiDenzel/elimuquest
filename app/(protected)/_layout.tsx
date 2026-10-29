import { Redirect } from 'expo-router';
import { Stack } from 'expo-router/js-stack';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { colors } from '../../src/theme';
import { useAuthStore } from '../../src/stores/authStore';

export default function ProtectedLayout() {
  const user = useAuthStore((state) => state.user);
  const hydrated = useAuthStore((state) => state.hydrated);

  if (!hydrated) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (!user) return <Redirect href="/(auth)/welcome" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
