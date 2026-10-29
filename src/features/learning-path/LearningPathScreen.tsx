import { useLocalSearchParams } from 'expo-router';
import { Link } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { ScreenShell } from '../../components/layout/ScreenShell';
import { colors, radii, spacing } from '../../theme';
import { api } from '../../services/api/client';
import { QueryState } from '../../components/ui/QueryState';

export default function LearningPathScreen() {
  const { subjectId } = useLocalSearchParams<{ subjectId: string }>();
  const path = useQuery({
    queryKey: ['learning-path', subjectId],
    queryFn: () => api.learningPath(subjectId),
    enabled: !!subjectId,
  });

  if (path.isPending || path.isError) {
    return (
      <ScreenShell>
        <QueryState loading={path.isPending} error={path.error?.message} onRetry={() => void path.refetch()} />
      </ScreenShell>
    );
  }
  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.eyebrow}>Learning path</Text>
        <Text style={styles.title}>{path.data.subject}</Text>
        <Text style={styles.curriculum}>{path.data.curriculum_label}</Text>
        {path.data.lessons.length === 0 ? (
          <View style={styles.card}><Text style={styles.cardText}>No published lessons are available yet.</Text></View>
        ) : path.data.lessons.map((lesson, index) => (
          <View key={lesson.id} style={styles.lessonCard}>
            <Text style={styles.lessonNumber}>LESSON {index + 1}{lesson.completed ? ' · COMPLETED' : ''}</Text>
            <Text style={styles.lessonTitle}>{lesson.title}</Text>
            <Text style={styles.cardText}>{lesson.description}</Text>
            <Link href={{ pathname: '/lesson/[lessonId]', params: { lessonId: lesson.id } }} asChild>
              <Pressable style={styles.button}><Text style={styles.buttonText}>{lesson.completed ? 'Review lesson' : 'Start lesson'}</Text></Pressable>
            </Link>
          </View>
        ))}
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
  lessonCard: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    padding: spacing.xl,
    marginBottom: spacing.md,
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
  lessonNumber: { color: colors.primary, fontSize: 12, fontWeight: '700', marginBottom: spacing.sm },
  curriculum: { color: colors.textSoft, marginBottom: spacing.lg },
  lessonTitle: { color: colors.text, fontSize: 20, fontWeight: '800', marginBottom: spacing.sm },
  button: { marginTop: spacing.md, backgroundColor: colors.primary, padding: spacing.md, borderRadius: radii.md, alignItems: 'center' },
  buttonText: { color: colors.white, fontWeight: '700' },
});
