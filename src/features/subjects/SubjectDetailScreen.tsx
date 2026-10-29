import { useLocalSearchParams } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Link } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ScreenShell } from '../../components/layout/ScreenShell';
import { colors, radii, spacing } from '../../theme';
import { api } from '../../services/api/client';
import { QueryState } from '../../components/ui/QueryState';

export default function SubjectDetailScreen() {
  const { subjectId } = useLocalSearchParams<{ subjectId: string }>();
  const subject = useQuery({
    queryKey: ['subject', subjectId],
    queryFn: () => api.subject(subjectId),
    enabled: !!subjectId,
  });

  if (subject.isPending || subject.isError) {
    return (
      <ScreenShell>
        <QueryState loading={subject.isPending} error={subject.error?.message} onRetry={() => void subject.refetch()} />
      </ScreenShell>
    );
  }
  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.eyebrow}>Subject</Text>
        <Text style={styles.title}>{subject.data.name}</Text>
        <View style={styles.card}>
          <Text style={styles.curriculum}>{subject.data.curriculum_label}</Text>
          <Text style={styles.cardText}>{subject.data.description || `Continue your ${subject.data.name} learning journey.`}</Text>
          {subject.data.ready ? (
            <Text style={styles.progress}>Your mastery: {subject.data.progress}%</Text>
          ) : (
            <Text style={styles.empty}>No published lessons are available yet.</Text>
          )}
          <Text style={styles.meta}>
            {subject.data.ready ? `${subject.data.lessons} published lessons` : 'Curriculum source recorded; topic mapping is pending review.'}
          </Text>
          {subject.data.next_lesson && <Text style={styles.meta}>Next up: {subject.data.next_lesson}</Text>}
          <Link href={{ pathname: '/learning-path/[subjectId]', params: { subjectId: subject.data.id } }} asChild>
            <Pressable style={styles.button}><Text style={styles.buttonText}>View learning path</Text></Pressable>
          </Link>
        </View>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: spacing.xl,
    width: '100%',
    maxWidth: 760,
    alignSelf: 'center',
  },
  eyebrow: {
    color: colors.primary,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.text,
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardText: {
    color: colors.textSoft,
    fontSize: 16,
    lineHeight: 24,
  },
  curriculum: { color: colors.primary, fontWeight: '800', marginBottom: spacing.sm },
  empty: { color: colors.textSoft, fontWeight: '700', marginTop: spacing.lg },
  progress: { color: colors.primary, fontSize: 16, fontWeight: '700', marginTop: spacing.lg },
  meta: { color: colors.textSoft, marginTop: spacing.sm },
  button: { marginTop: spacing.xl, backgroundColor: colors.primary, padding: spacing.md, borderRadius: radii.md, alignItems: 'center' },
  buttonText: { color: colors.white, fontWeight: '700' },
});
