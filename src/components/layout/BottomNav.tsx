import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Home, BookOpen, BarChart3, Trophy, User } from 'lucide-react-native';
import { colors, radii, shadow, spacing } from '../../theme';

type TabKey = 'learn' | 'practice' | 'progress' | 'leaderboard' | 'profile';

type BottomNavProps = {
  activeTab: TabKey;
  onTabPress: (tab: TabKey) => void;
};

const tabs: Array<{ key: TabKey; label: string; icon: typeof Home }> = [
  { key: 'learn', label: 'Learn', icon: Home },
  { key: 'practice', label: 'Practice', icon: BookOpen },
  { key: 'progress', label: 'Progress', icon: BarChart3 },
  { key: 'leaderboard', label: 'League', icon: Trophy },
  { key: 'profile', label: 'Profile', icon: User },
];

export function BottomNav({ activeTab, onTabPress }: BottomNavProps) {
  return (
    <View style={[styles.container, shadow.soft]}>
      {tabs.map(({ key, label, icon: Icon }) => {
        const isActive = activeTab === key;
        return (
          <Pressable
            key={key}
            onPress={() => onTabPress(key)}
            style={styles.tab}
            accessibilityRole="button"
            accessibilityLabel={label}
          >
            <View style={[styles.iconWrap, isActive && styles.activeIconWrap]}>
              <Icon size={18} color={isActive ? colors.primary : colors.textSoft} />
            </View>
            <Text style={[styles.label, isActive && styles.activeLabel]}>{label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: colors.white,
    borderTopLeftRadius: radii.xl,
    borderTopRightRadius: radii.xl,
    paddingTop: spacing.md,
    paddingBottom: spacing.lg,
    paddingHorizontal: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  tab: {
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
    color: colors.textSoft,
    fontWeight: '600',
  },
  activeLabel: {
    color: colors.primary,
  },
});
