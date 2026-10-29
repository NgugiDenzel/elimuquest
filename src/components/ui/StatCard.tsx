import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radii, shadow, spacing } from '../../theme';

type StatCardProps = {
  value: string;
  label: string;
  accent?: string;
  icon?: React.ReactNode;
};

export function StatCard({ value, label, accent = colors.primary, icon }: StatCardProps) {
  return (
    <View style={[styles.card, shadow.soft, { borderColor: accent + '20' }]}>
      <View style={[styles.iconWrap, { backgroundColor: accent + '15' }]}>{icon}</View>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: 94,
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    padding: spacing.md,
    justifyContent: 'center',
  },
  value: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    marginTop: spacing.sm,
  },
  label: {
    fontSize: 12,
    color: colors.textSoft,
    marginTop: 4,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
