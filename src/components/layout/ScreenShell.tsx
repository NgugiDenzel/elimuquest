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
        <View style={styles.content}>{children}</View>
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
    flexGrow: 1,
    paddingBottom: 20,
  },
  content: {
    width: '100%',
    maxWidth: 1120,
    alignSelf: 'center',
    flexGrow: 1,
  },
  withBottomNav: {
    paddingBottom: 120,
  },
});
