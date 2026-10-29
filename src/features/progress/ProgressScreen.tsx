import React from 'react';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { colors, radii, shadow, spacing } from '../../theme';
import { ScreenShell } from '../../components/layout/ScreenShell';
import { QueryState } from '../../components/ui/QueryState';
import { api } from '../../services/api/client';

export function ProgressScreen() {
  const { width } = useWindowDimensions();
  const isWide = width >= 900;
  const progress = useQuery({ queryKey: ['progress'], queryFn: api.progress });

  if (progress.isPending || progress.isError) {
    return (
      <ScreenShell withBottomNav>
        <QueryState loading={progress.isPending} error={progress.error?.message} onRetry={() => void progress.refetch()} />
      </ScreenShell>
    );
  }

  const data = progress.data;
  const maxActivity = Math.max(...data.weekly_activity.map((item) => item.xp), 1);

  return (
    <ScreenShell withBottomNav>
      <View style={[styles.container, isWide && styles.wideContainer]}>
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.heading}>Progress</Text>
            <Text style={styles.subtitle}>Small steps add up. Keep your momentum.</Text>
          </View>
          <View style={styles.avatar}><Text style={styles.avatarText}>✓</Text></View>
        </View>

        <View style={styles.statsRow}>
          <View style={[styles.summaryCard, shadow.soft]}>
            <Text style={styles.summaryValue}>{data.total_xp.toLocaleString()}</Text>
            <Text style={styles.summaryLabel}>Total XP</Text>
          </View>
          <View style={[styles.summaryCard, shadow.soft]}>
            <Text style={styles.summaryValue}>{data.lessons_completed}</Text>
            <Text style={styles.summaryLabel}>Lessons completed</Text>
          </View>
          <View style={[styles.summaryCard, shadow.soft]}>
            <Text style={styles.summaryValue}>{data.accuracy}%</Text>
            <Text style={styles.summaryLabel}>Accuracy</Text>
          </View>
        </View>

        <View style={[styles.sectionCard, shadow.soft]}>
          <View style={styles.chartHeader}>
            <Text style={styles.sectionTitle}>Weekly activity</Text>
            <Text style={styles.chartCaption}>XP earned</Text>
          </View>
          <View style={styles.barChart}>
            {data.weekly_activity.map((bar, index) => (
              <View key={`${bar.label}-${index}`} style={styles.barColumn}>
                <Text style={styles.barValue}>{bar.xp || ''}</Text>
                <View style={styles.barTrack}>
                  <View style={[
                    styles.bar,
                    { height: `${Math.max(bar.xp ? bar.xp / maxActivity * 100 : 4, 4)}%` },
                    index === data.weekly_activity.length - 1 && styles.currentBar,
                  ]} />
                </View>
                <Text style={styles.barLabel}>{bar.label}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={[styles.sectionCard, shadow.soft]}>
          <Text style={styles.sectionTitle}>Subject mastery</Text>
          {data.mastery.length === 0 ? (
            <Text style={styles.emptyText}>Subject progress will appear as you complete lessons.</Text>
          ) : data.mastery.map((item) => (
            <View key={item.subject} style={styles.masteryRow}>
              <Text style={styles.subjectTitle}>{item.subject}</Text>
              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: `${item.progress}%`, backgroundColor: item.accent }]} />
              </View>
              <Text style={styles.subjectValue}>{item.progress}%</Text>
            </View>
          ))}
        </View>

        <View style={styles.topicGrid}>
          <View style={[styles.topicCard, shadow.soft]}>
            <Text style={styles.sectionTitle}>Strongest topics</Text>
            {data.strongest_topics.length
              ? data.strongest_topics.map((topic) => <Text key={topic} style={styles.topicItem}>{topic}</Text>)
              : <Text style={styles.emptyText}>Complete more lessons to discover your strongest topics.</Text>}
          </View>
          <View style={[styles.topicCard, shadow.soft]}>
            <Text style={styles.sectionTitle}>Needs review</Text>
            {data.needs_review.length
              ? data.needs_review.map((topic) => <Text key={topic} style={styles.topicItem}>{topic}</Text>)
              : <Text style={styles.emptyText}>No review suggestions yet.</Text>}
          </View>
        </View>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: 120,
    width: '100%',
    maxWidth: 760,
    alignSelf: 'center',
  },
  wideContainer: { maxWidth: 1080, paddingHorizontal: 36, paddingTop: 40 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xl },
  heading: { fontSize: 30, fontWeight: '800', color: colors.text },
  subtitle: { color: colors.textSoft, marginTop: 4 },
  avatar: { width: 42, height: 42, borderRadius: 21, backgroundColor: colors.greenSoft, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: colors.green, fontWeight: '800', fontSize: 18 },
  statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.xl },
  summaryCard: { flex: 1, backgroundColor: colors.card, borderRadius: radii.lg, paddingVertical: spacing.md, paddingHorizontal: spacing.sm, alignItems: 'center' },
  summaryValue: { fontSize: 22, fontWeight: '800', color: colors.text },
  summaryLabel: { marginTop: 4, fontSize: 12, color: colors.textSoft, textAlign: 'center' },
  sectionCard: { backgroundColor: colors.card, borderRadius: radii.xl, padding: spacing.lg, marginBottom: spacing.xl },
  chartHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sectionTitle: { fontSize: 18, fontWeight: '800', color: colors.text, marginBottom: spacing.md },
  chartCaption: { color: colors.textSoft, fontSize: 12, marginBottom: spacing.md },
  barChart: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', height: 145, gap: spacing.sm },
  barColumn: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', height: 145 },
  barValue: { minHeight: 15, color: colors.textSoft, fontSize: 10, marginBottom: 4 },
  barTrack: { width: '70%', flex: 1, alignItems: 'center', justifyContent: 'flex-end', backgroundColor: '#F0F4FA', borderRadius: 999, overflow: 'hidden' },
  bar: { width: '100%', backgroundColor: '#9FC5FF', borderRadius: 999, minHeight: 4 },
  currentBar: { backgroundColor: colors.primary },
  barLabel: { fontSize: 11, marginTop: 7, color: colors.textSoft },
  masteryRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
  subjectTitle: { width: 90, color: colors.text, fontWeight: '600' },
  progressTrack: { flex: 1, height: 9, backgroundColor: '#E7EFFB', borderRadius: 999, overflow: 'hidden', marginHorizontal: spacing.sm },
  progressFill: { height: '100%', borderRadius: 999 },
  subjectValue: { width: 42, textAlign: 'right', color: colors.text, fontWeight: '700' },
  topicGrid: { flexDirection: 'row', gap: spacing.md },
  topicCard: { flex: 1, backgroundColor: colors.card, borderRadius: radii.xl, padding: spacing.lg },
  topicItem: { color: colors.textSoft, marginBottom: 8, fontSize: 13 },
  emptyText: { color: colors.textSoft, fontSize: 13, lineHeight: 20 },
});
