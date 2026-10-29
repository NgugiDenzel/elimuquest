import { StyleSheet, Text, View } from 'react-native';
import { Pressable } from 'react-native';
import { router } from 'expo-router';
import { ScreenShell } from '../../src/components/layout/ScreenShell';
import { colors, radii, spacing } from '../../src/theme';
import { useAuthStore } from '../../src/stores/authStore';
import { useAuthActions } from '../../src/hooks/useAuth';

export default function ProfileRoute() {
  const user = useAuthStore((state) => state.user);
  const { logout } = useAuthActions();

  const signOut = async () => {
    await logout();
    router.replace('/(auth)/welcome');
  };

  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.title}>Profile</Text>
        <View style={styles.card}>
          <Text style={styles.avatar}>A</Text>
          <Text style={styles.name}>{user?.full_name}</Text>
          <Text style={styles.meta}>
            {user?.curriculum_level} · {user?.curriculum_system === 'CBC_CBE' ? 'CBC/CBE' : user?.curriculum_system === '8_4_4' ? '8-4-4' : 'Choose curriculum'}
          </Text>
          <Text style={styles.meta}>{user?.email}</Text>
        </View>
        {user?.role === 'admin' && (
          <Pressable
            style={styles.adminButton}
            onPress={() => router.push('/(tabs)/admin')}
            accessibilityRole="button"
          >
            <Text style={styles.adminButtonText}>Review curriculum content</Text>
          </Pressable>
        )}
        <Pressable style={styles.logoutButton} onPress={() => void signOut()} accessibilityRole="button">
          <Text style={styles.logoutText}>Log out</Text>
        </Pressable>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: spacing.xl,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.lg,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  avatar: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: colors.primarySoft,
    color: colors.primary,
    textAlign: 'center',
    lineHeight: 70,
    fontSize: 28,
    fontWeight: '700',
    marginBottom: spacing.md,
  },
  name: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.text,
  },
  meta: {
    color: colors.textSoft,
    marginTop: 6,
  },
  logoutButton: {
    marginTop: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
    paddingVertical: spacing.md,
    borderRadius: radii.md,
    alignItems: 'center',
  },
  adminButton: {
    marginTop: spacing.lg,
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    borderRadius: radii.md,
    alignItems: 'center',
  },
  adminButtonText: { color: colors.white, fontWeight: '700' },
  logoutText: { color: colors.red, fontWeight: '700' },
});
