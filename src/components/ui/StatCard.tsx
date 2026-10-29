import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radii, shadow, spacing } from '../../theme';

type StatCardProps = {
  value: string;
  label: string;
  accent?: string;
  icon?: React.ReactNode;
  dense?: boolean;
};

export function StatCard({ value, label, accent = colors.primary, icon, dense = false }: StatCardProps) {
  return (
    <View style={[styles.card, dense && styles.denseCard, shadow.soft, { borderColor: accent + '20' }]}>
      <View style={[styles.iconWrap, { backgroundColor: accent + '15' }]}>{icon}</View>
      <Text style={[styles.value, dense && styles.denseValue]} numberOfLines={1} adjustsFontSizeToFit>
        {value}
      </Text>
      <Text style={styles.label} numberOfLines={2}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: 0,
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    padding: spacing.md,
    justifyContent: 'center',
  },
  denseCard: {
    padding: spacing.sm,
  },
  value: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    marginTop: spacing.sm,
  },
  denseValue: {
    fontSize: 19,
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
