import { Tabs, type BottomTabBarProps } from 'expo-router/js-tabs';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { BarChart3, BookOpen, Home, Trophy, User } from 'lucide-react-native';
import React from 'react';
import { colors, radii, shadow, spacing } from '../../src/theme';
import { Redirect } from 'expo-router';
import { ActivityIndicator } from 'react-native';
import { useAuthStore } from '../../src/stores/authStore';

const tabItems = [
  { key: 'index', label: 'Learn', icon: Home },
  { key: 'practice', label: 'Practice', icon: BookOpen },
  { key: 'progress', label: 'Progress', icon: BarChart3 },
  { key: 'leaderboard', label: 'League', icon: Trophy },
  { key: 'profile', label: 'Profile', icon: User },
] as const;

function TabBar({ state, navigateToTab }: BottomTabBarProps) {
  return (
    <View style={[styles.tabBar, shadow.soft]}>
      {tabItems.map((item, index) => {
        const isActive = state.index === index;
        const Icon = item.icon;

        return (
          <Pressable
            key={item.key}
            accessibilityRole="button"
            accessibilityLabel={item.label}
            style={styles.tabButton}
            onPress={() => navigateToTab(state.routes[index].key)}
          >
            <View style={[styles.iconWrap, isActive && styles.activeIconWrap]}>
              <Icon size={18} color={isActive ? colors.primary : colors.textSoft} />
            </View>
            <Text style={[styles.label, isActive && styles.activeLabel]}>{item.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export default function TabsLayout() {
  const user = useAuthStore((state) => state.user);
  const hydrated = useAuthStore((state) => state.hydrated);
  if (!hydrated) return <ActivityIndicator color={colors.primary} />;
  if (!user) return <Redirect href="/(auth)/welcome" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: { display: 'none' },
      }}
      tabBar={(props) => <TabBar {...props} />}
    >
      <Tabs.Screen name="index" options={{ title: 'Learn' }} />
      <Tabs.Screen name="practice" options={{ title: 'Practice' }} />
      <Tabs.Screen name="progress" options={{ title: 'Progress' }} />
      <Tabs.Screen name="leaderboard" options={{ title: 'League' }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} />
      <Tabs.Screen name="admin" options={{ href: null }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    position: 'absolute',
    left: 18,
    right: 18,
    bottom: 14,
    maxWidth: 720,
    alignSelf: 'center',
    flexDirection: 'row',
    backgroundColor: colors.white,
    borderRadius: radii.xl,
    borderWidth: 1,
    borderColor: colors.border,
    paddingTop: spacing.md,
    paddingBottom: spacing.lg,
    paddingHorizontal: spacing.sm,
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeIconWrap: {
    backgroundColor: colors.primarySoft,
  },
  label: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSoft,
  },
  activeLabel: {
    color: colors.primary,
  },
});
