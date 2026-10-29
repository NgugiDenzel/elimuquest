import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../../theme';

type QueryStateProps = {
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
};

export function QueryState({ loading, error, onRetry }: QueryStateProps) {
  if (loading) {
    return (
      <View style={styles.container} accessibilityRole="progressbar">
        <ActivityIndicator color={colors.primary} />
        <Text style={styles.message}>Loading your learning data…</Text>
      </View>
    );
  }
  if (!error) return null;
  return (
    <View style={styles.container} accessibilityRole="alert">
      <Text style={styles.message}>{error}</Text>
      {onRetry && (
        <Pressable style={styles.button} onPress={onRetry} accessibilityRole="button">
          <Text style={styles.buttonText}>Try again</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    gap: spacing.md,
  },
  message: {
    color: colors.textSoft,
    textAlign: 'center',
    lineHeight: 22,
  },
  button: {
    backgroundColor: colors.primary,
    paddingVertical: 12,
    paddingHorizontal: spacing.xl,
    borderRadius: radii.md,
  },
  buttonText: {
    color: colors.white,
    fontWeight: '700',
  },
});
