import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../../theme';

type ScreenShellProps = {
  children: React.ReactNode;
  withBottomNav?: boolean;
};

export function ScreenShell({ children, withBottomNav = false }: ScreenShellProps) {
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={[styles.scrollContent, withBottomNav && styles.withBottomNav]}
        showsVerticalScrollIndicator={false}
      >
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  withBottomNav: {
    paddingBottom: 120,
  },
});
