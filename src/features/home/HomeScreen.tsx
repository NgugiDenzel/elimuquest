import React from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Bell, Flame, Medal, Sparkles, Target, TrendingUp } from 'lucide-react-native';
import { router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { colors, radii, shadow, spacing } from '../../theme';
import { StatCard } from '../../components/ui/StatCard';
import { QueryState } from '../../components/ui/QueryState';
import { api } from '../../services/api/client';
import { useAuthStore } from '../../stores/authStore';

const subjectGradient: Record<string, string> = {
  biology: '#EAF8EE',
  chemistry: '#EDF3FF',
  physics: '#FFF8E8',
  math: '#FFF0F6',
};

export function HomeScreen() {
  const { width } = useWindowDimensions();
  const isWide = width >= 900;
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);
  const dashboard = useQuery({ queryKey: ['dashboard'], queryFn: api.dashboard });
  const curricula = useQuery({ queryKey: ['curricula'], queryFn: api.curricula });
  const selectCurriculum = useMutation({
    mutationFn: (selection: { curriculum_system: string; curriculum_level: string }) =>
      api.updateProfile(selection),
    onSuccess: async (profile) => {
      setUser(profile);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
        queryClient.invalidateQueries({ queryKey: ['subjects'] }),
        queryClient.invalidateQueries({ queryKey: ['progress'] }),
      ]);
    },
  });

  if (dashboard.isPending || dashboard.isError) {
    return (
      <View style={styles.queryContainer}>
        <QueryState
          loading={dashboard.isPending}
          error={dashboard.error?.message}
          onRetry={() => void dashboard.refetch()}
        />
      </View>
    );
  }
  const data = dashboard.data;
  if (!data) {
    return (
      <View style={styles.queryContainer}>
        <QueryState error="Dashboard data is unavailable." />
      </View>
    );
  }
  const goalProgress = Math.min(
    100,
    Math.round((data.daily_progress_xp * 100) / Math.max(data.daily_goal_xp, 1)),
  );
  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={[styles.content, isWide && styles.wideContent]} showsVerticalScrollIndicator={false}>
        <View style={styles.topBar}>
          <View style={styles.avatarWrap}>
            <Text style={styles.avatar}>A</Text>
          </View>
          <View style={styles.greetingWrap}>
            <Text style={styles.caption}>Welcome back</Text>
            <Text style={styles.title}>Habari, {data.student.full_name.split(' ')[0]}!</Text>
          </View>
          <Pressable style={styles.notifyButton} accessibilityRole="button" accessibilityLabel="Notifications">
            <Bell size={18} color={colors.text} />
          </Pressable>
        </View>

        <View style={styles.curriculumCard}>
          <Text style={styles.curriculumTitle}>Your curriculum</Text>
          <Text style={styles.curriculumHint}>
            {data.student.curriculum_system === 'LEGACY'
              ? 'Choose the programme and level you are studying.'
              : `Selected: ${curricula.data?.items.find((item) =>
                  item.system === data.student.curriculum_system &&
                  item.level === data.student.curriculum_level)?.label ?? data.student.curriculum_level}`}
          </Text>
          {curricula.isPending ? (
            <ActivityIndicator color={colors.primary} accessibilityLabel="Loading curriculum choices" />
          ) : curricula.isError ? (
            <Pressable onPress={() => void curricula.refetch()} accessibilityRole="button">
              <Text style={styles.curriculumError}>Could not load choices. Tap to retry.</Text>
            </Pressable>
          ) : (
            <View style={styles.curriculumOptions}>
              {curricula.data.items.map((option) => {
                const selected = data.student.curriculum_system === option.system &&
                  data.student.curriculum_level === option.level;
                return (
                  <Pressable
                    key={`${option.system}-${option.level}`}
                    accessibilityRole="button"
                    accessibilityState={{ selected, disabled: selectCurriculum.isPending }}
                    disabled={selectCurriculum.isPending || selected}
                    onPress={() => selectCurriculum.mutate({
                      curriculum_system: option.system,
                      curriculum_level: option.level,
                    })}
                    style={[styles.curriculumChip, selected && styles.curriculumChipSelected]}
                  >
                    <Text style={[styles.curriculumChipText, selected && styles.curriculumChipTextSelected]}>
                      {option.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
          {selectCurriculum.isPending && <Text style={styles.curriculumHint}>Saving selection…</Text>}
          {!!selectCurriculum.error && (
            <Text style={styles.curriculumError} accessibilityRole="alert">
              {selectCurriculum.error.message}
            </Text>
          )}
        </View>

        <View style={[styles.statsRow, isWide && styles.wideStatsRow]}>
          <StatCard value={String(data.streak_days)} label="Day streak" accent={colors.green} icon={<Flame size={18} color={colors.green} />} />
          <StatCard value={data.total_xp.toLocaleString()} label="XP" accent={colors.primary} icon={<TrendingUp size={18} color={colors.primary} />} />
          <StatCard value={data.league_rank ? `#${data.league_rank}` : '—'} label="League" accent={colors.amber} icon={<Medal size={18} color={colors.amber} />} />
        </View>

        <View style={[styles.featureRow, isWide && styles.wideFeatureRow]}>
          <View style={[styles.goalCard, isWide && styles.wideFeatureCard]}>
            <View style={styles.goalHeader}>
              <View style={styles.goalTitleRow}>
                <View style={styles.goalIcon}>
                  <Target size={18} color={colors.sky} />
                </View>
                <Text style={styles.goalTitle}>Daily Goal</Text>
              </View>
              <Text style={styles.goalPercent}>{goalProgress}%</Text>
            </View>
            <Text style={styles.goalText}>Reach {data.daily_goal_xp} XP today</Text>
            <Text style={styles.goalHint}>{data.daily_progress_xp} of {data.daily_goal_xp} XP earned</Text>
            <View style={styles.progressWrapper}>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${goalProgress}%` }]} />
              </View>
              <View style={styles.goalCircle}>
                <Text style={styles.goalCircleText}>{goalProgress}%</Text>
              </View>
            </View>
          </View>

          <View style={[styles.questCard, isWide && styles.wideFeatureCard]}>
            <View style={styles.questTopRow}>
              <Text style={styles.questEyebrow}>Your current quest</Text>
              <View style={styles.questIcon}><Sparkles size={17} color={colors.primary} /></View>
            </View>
            {data.current_lesson ? (
              <>
                <View style={styles.questHeader}>
                  <View style={styles.questSubjectBadge}><Text style={styles.questSubjectText}>{data.current_lesson.subject}</Text></View>
                  <Text style={styles.questMeta}>{data.current_lesson.topic}</Text>
                </View>
                <Text style={styles.questTitle}>{data.current_lesson.title}</Text>
                <Text style={styles.questDetail}>{data.current_lesson.description}</Text>
                <Pressable
                  style={styles.primaryButton}
                  accessibilityRole="button"
                  onPress={() => router.push({ pathname: '/(tabs)/lesson/[lessonId]', params: { lessonId: data.current_lesson?.id ?? '' } })}
                >
                  <Text style={styles.primaryButtonText}>Start Lesson</Text>
                </Pressable>
              </>
            ) : (
              <Text style={styles.questDetail}>You’ve completed all available lessons. Check back for new learning quests.</Text>
            )}
          </View>
        </View>

        <View style={styles.subjectHeader}>
          <Text style={styles.sectionTitle}>Subjects</Text>
          <Text style={styles.link}>Browse all</Text>
        </View>

        <View style={[styles.subjectGrid, isWide && styles.wideSubjectGrid]}>
          {data.subjects.map((subject) => (
            <Pressable
              key={subject.id}
              accessibilityRole="button"
              accessibilityLabel={`Open ${subject.name}`}
              onPress={() => router.push({ pathname: '/subjects/[subjectId]', params: { subjectId: subject.id } })}
              style={[styles.subjectCard, isWide && styles.wideSubjectCard, { backgroundColor: subjectGradient[subject.id] ?? '#EEF4FF' }, shadow.soft]}
            >
              <View style={[styles.subjectIconWrap, { backgroundColor: `${subject.accent}18` }]}>
                <Text style={styles.subjectEmoji}>{subject.icon}</Text>
              </View>
              <Text style={styles.subjectName}>{subject.name}</Text>
              <Text style={styles.subjectMeta}>
                {subject.ready
                  ? `Next up · ${subject.next_lesson ?? 'Review a lesson'}`
                  : `${subject.curriculum_label} · No published lessons yet`}
              </Text>
              {subject.ready && (
                <View style={styles.subjectProgressRow}>
                  <View style={styles.subjectBar}>
                    <View style={[styles.subjectFill, { width: `${subject.progress}%`, backgroundColor: subject.accent }]} />
                  </View>
                  <Text style={styles.subjectPercent}>{subject.progress}%</Text>
                </View>
              )}
            </Pressable>
          ))}
        </View>
        {data.subjects.length === 0 && (
          <View style={styles.emptySubjects}>
            <Text style={styles.emptySubjectsTitle}>Subjects are being prepared</Text>
            <Text style={styles.emptySubjectsText}>
              There are no subject records for this selection yet. No lessons or progress are being assumed.
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  queryContainer: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  screen: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  content: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: 150,
    width: '100%',
    maxWidth: 760,
    alignSelf: 'center',
  },
  wideContent: {
    maxWidth: 1160,
    paddingHorizontal: 36,
    paddingTop: 40,
    paddingBottom: 140,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  curriculumCard: {
    backgroundColor: colors.white,
    borderRadius: radii.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.xl,
  },
  curriculumTitle: { color: colors.text, fontSize: 16, fontWeight: '800' },
  curriculumHint: { color: colors.textSoft, fontSize: 13, marginTop: spacing.xs, marginBottom: spacing.sm },
  curriculumOptions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  curriculumChip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.canvas,
  },
  curriculumChipSelected: { borderColor: colors.primary, backgroundColor: colors.primarySoft },
  curriculumChipText: { color: colors.textSoft, fontWeight: '700', fontSize: 13 },
  curriculumChipTextSelected: { color: colors.primary },
  curriculumError: { color: colors.red, fontSize: 13, marginTop: spacing.xs },
  emptySubjects: {
    backgroundColor: colors.white,
    borderRadius: radii.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.xl,
    marginTop: spacing.md,
  },
  emptySubjectsTitle: { color: colors.text, fontSize: 16, fontWeight: '800' },
  emptySubjectsText: { color: colors.textSoft, lineHeight: 22, marginTop: spacing.xs },
  avatarWrap: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.primarySoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatar: {
    fontSize: 18,
    color: colors.primary,
    fontWeight: '800',
  },
  greetingWrap: {
    flex: 1,
    marginLeft: spacing.md,
  },
  caption: {
    fontSize: 12,
    color: colors.textSoft,
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: colors.text,
  },
  notifyButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadow.soft,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  wideStatsRow: {
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  featureRow: {
    gap: spacing.md,
    marginBottom: spacing.xl,
  },
  wideFeatureRow: {
    flexDirection: 'row',
    alignItems: 'stretch',
    marginBottom: spacing.md,
  },
  goalCard: {
    backgroundColor: colors.navy,
    borderRadius: radii.xl,
    padding: spacing.xl,
    marginBottom: 0,
  },
  wideFeatureCard: {
    flex: 1,
    minWidth: 0,
    marginBottom: spacing.lg,
    justifyContent: 'center',
  },
  goalTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  goalIcon: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: '#16314C',
    alignItems: 'center',
    justifyContent: 'center',
  },
  goalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  goalTitle: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '700',
  },
  goalPercent: {
    color: colors.sky,
    fontWeight: '700',
  },
  goalText: {
    color: '#D1DEFF',
    marginTop: spacing.md,
  },
  goalHint: {
    color: '#91A9C5',
    fontSize: 12,
    marginTop: 5,
  },
  progressWrapper: {
    marginTop: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  progressBar: {
    flex: 1,
    height: 10,
    backgroundColor: '#24415F',
    borderRadius: 999,
    overflow: 'hidden',
  },
  progressFill: {
    width: '72%',
    height: '100%',
    backgroundColor: colors.sky,
    borderRadius: 999,
  },
  goalCircle: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: '#16314C',
    borderWidth: 4,
    borderColor: colors.sky,
    alignItems: 'center',
    justifyContent: 'center',
  },
  goalCircleText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '700',
  },
  questCard: {
    backgroundColor: colors.white,
    borderRadius: radii.xl,
    padding: spacing.xl,
    marginBottom: 0,
    ...shadow.soft,
  },
  questTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  questIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: colors.primarySoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  questEyebrow: {
    color: colors.textSoft,
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  questHeader: {
    marginTop: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  questSubjectBadge: {
    backgroundColor: colors.primarySoft,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  questSubjectText: {
    color: colors.primary,
    fontWeight: '700',
    fontSize: 12,
  },
  questMeta: {
    color: colors.textSoft,
    fontWeight: '600',
  },
  questTitle: {
    marginTop: spacing.md,
    color: colors.text,
    fontSize: 24,
    fontWeight: '800',
  },
  questDetail: {
    color: colors.textSoft,
    fontSize: 13,
  },
  questDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.md,
  },
  questProgressLabel: {
    color: colors.primary,
    fontWeight: '700',
    fontSize: 13,
  },
  questProgressBar: {
    marginTop: spacing.sm,
    height: 10,
    backgroundColor: '#E9EEF7',
    borderRadius: 999,
    overflow: 'hidden',
  },
  questProgressFill: {
    width: '68%',
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 999,
  },
  primaryButton: {
    marginTop: spacing.lg,
    backgroundColor: colors.primary,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  subjectHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text,
  },
  link: {
    color: colors.primary,
    fontWeight: '700',
  },
  subjectGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  wideSubjectGrid: {
    flexWrap: 'nowrap',
  },
  subjectCard: {
    width: '48%',
    borderRadius: radii.xl,
    padding: spacing.lg,
    minHeight: 170,
    ...shadow.soft,
  },
  wideSubjectCard: {
    width: '24%',
  },
  subjectIconWrap: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  subjectEmoji: {
    fontSize: 22,
  },
  subjectName: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
  },
  subjectMeta: {
    color: colors.textSoft,
    marginTop: 8,
    marginBottom: spacing.md,
    fontSize: 12,
  },
  subjectProgressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  subjectBar: {
    flex: 1,
    height: 8,
    backgroundColor: 'rgba(16,32,51,0.12)',
    borderRadius: 999,
    overflow: 'hidden',
  },
  subjectFill: {
    height: '100%',
    borderRadius: 999,
  },
  subjectPercent: {
    fontWeight: '700',
    color: colors.text,
    fontSize: 12,
  },
});
