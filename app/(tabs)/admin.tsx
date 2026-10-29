import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { QueryState } from '../../src/components/ui/QueryState';
import { ScreenShell } from '../../src/components/layout/ScreenShell';
import { api } from '../../src/services/api/client';
import type { AdminLesson } from '../../src/services/api/types';
import { colors, radii, spacing } from '../../src/theme';

const nextStates: Record<AdminLesson['status'], Array<{ label: string; status: AdminLesson['status'] }>> = {
  draft: [{ label: 'Submit for review', status: 'in_review' }],
  in_review: [
    { label: 'Return to draft', status: 'draft' },
    { label: 'Approve', status: 'approved' },
  ],
  approved: [
    { label: 'Request changes', status: 'in_review' },
    { label: 'Publish', status: 'published' },
  ],
  published: [{ label: 'Archive', status: 'archived' }],
  archived: [{ label: 'Restore to draft', status: 'draft' }],
};

export default function AdminContentScreen() {
  const queryClient = useQueryClient();
  const lessons = useQuery({ queryKey: ['admin-lessons'], queryFn: api.adminLessons });
  const changeStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: AdminLesson['status'] }) =>
      api.updateLessonStatus(id, status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin-lessons'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  if (lessons.isPending || lessons.isError) {
    return (
      <ScreenShell>
        <QueryState
          loading={lessons.isPending}
          error={lessons.error?.message}
          onRetry={() => void lessons.refetch()}
        />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.eyebrow}>Content administration</Text>
        <Text style={styles.title}>Review curriculum content</Text>
        <Text style={styles.intro}>
          Confirm source citations, curriculum mapping, accuracy, and learner suitability before approval.
          Publishing makes a lesson visible to its selected level.
        </Text>
        {lessons.data.items.length === 0 ? (
          <View style={styles.card}>
            <Text style={styles.cardText}>No content packages have been imported.</Text>
          </View>
        ) : lessons.data.items.map((lesson) => (
          <View key={lesson.id} style={styles.card}>
            <View style={styles.statusRow}>
              <Text style={styles.status}>{lesson.status.replace('_', ' ').toUpperCase()}</Text>
              {lesson.is_demo && <Text style={styles.demo}>DEMO</Text>}
            </View>
            <Text style={styles.lessonTitle}>{lesson.title}</Text>
            <Text style={styles.meta}>Content version {lesson.content_version}</Text>
            <Text style={styles.meta}>
              Curriculum alignment: {lesson.curriculum_alignment ?? 'unverified'} · Quality: {lesson.quality_status ?? 'needs_review'}
            </Text>
            {lesson.ai_generated && (
              <Text style={styles.aiNotice}>
                AI-assisted draft · requires human source verification and subject review
              </Text>
            )}
            <Text style={styles.meta}>
              {lesson.curriculum_level} · {lesson.curriculum_system} · {lesson.subject} · {lesson.topic}
            </Text>
            <Text style={styles.cardText}>{lesson.description}</Text>
            {!!lesson.content && (
              <>
                <Text style={styles.sectionTitle}>Lesson content</Text>
                <Text style={styles.cardText}>{lesson.content}</Text>
              </>
            )}
            {lesson.explanation_sections.map((section, index) => (
              <View key={`${lesson.id}-section-${index}`}>
                <Text style={styles.sectionTitle}>{section.title}</Text>
                <Text style={styles.cardText}>{section.body}</Text>
              </View>
            ))}
            {lesson.worked_examples.map((example, index) => (
              <View key={`${lesson.id}-example-${index}`}>
                <Text style={styles.sectionTitle}>Worked example {index + 1}</Text>
                <Text style={styles.cardText}>{example.prompt}</Text>
                <Text style={styles.cardText}>{example.solution}</Text>
                <Text style={styles.cardText}>{example.reasoning}</Text>
              </View>
            ))}
            <Text style={styles.sectionTitle}>Source</Text>
            <Text style={styles.cardText}>
              {lesson.source_id ?? 'No formal source ID'} · {lesson.source_reference ?? 'No page reference recorded'}
            </Text>
            {lesson.curriculum_alignment !== 'officially_verified' && (
              <Text style={styles.sourceNotice}>
                This content is being reviewed as {lesson.curriculum_alignment ?? 'unverified'} material.
                It may still be published when it passes the quality checks without a formal KICD citation.
              </Text>
            )}
            {lesson.source_reference?.includes('answer key absent from excerpt') && (
              <Text style={styles.sourceNotice}>
                The supplied excerpt omits its referenced answer key. Marking answers were
                calculated independently and need human verification.
              </Text>
            )}
            <Text style={styles.meta}>Author: {lesson.author ?? 'Not recorded'} · Reviewer: {lesson.reviewer ?? 'Not reviewed'}</Text>
            <Text style={styles.sectionTitle}>Learning objectives</Text>
            {lesson.learning_objectives.map((objective, index) => (
              <Text key={`${lesson.id}-objective-${index}`} style={styles.cardText}>- {objective}</Text>
            ))}
            <Text style={styles.sectionTitle}>Questions and answer keys (admin only)</Text>
            {lesson.questions.map((question, index) => (
              <View key={`${lesson.id}-question-${index}`} style={styles.question}>
                <Text style={styles.cardText}>{question.prompt}</Text>
                <Text style={styles.meta}>
                  {question.question_type.replace('_', ' ')} · Answer: {question.correct_answer} · {question.difficulty}
                </Text>
                {question.options.length > 0 && (
                  <Text style={styles.cardText}>Options: {question.options.join(' · ')}</Text>
                )}
                <Text style={styles.cardText}>{question.explanation}</Text>
              </View>
            ))}
            {nextStates[lesson.status].map((action) => (
              <Pressable
                key={action.status}
                accessibilityRole="button"
                disabled={changeStatus.isPending}
                onPress={() => changeStatus.mutate({ id: lesson.id, status: action.status })}
                style={[styles.button, changeStatus.isPending && styles.disabled]}
              >
                <Text style={styles.buttonText}>{action.label}</Text>
              </Pressable>
            ))}
          </View>
        ))}
        {!!changeStatus.error && (
          <Text style={styles.error} accessibilityRole="alert">{changeStatus.error.message}</Text>
        )}
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  container: { width: '100%', maxWidth: 820, alignSelf: 'center', padding: spacing.xl },
  eyebrow: { color: colors.primary, fontWeight: '800', textTransform: 'uppercase' },
  title: { color: colors.text, fontSize: 28, fontWeight: '800', marginTop: spacing.sm },
  intro: { color: colors.textSoft, lineHeight: 22, marginVertical: spacing.lg },
  card: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.xl,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  statusRow: { flexDirection: 'row', justifyContent: 'space-between' },
  status: { color: colors.primary, fontSize: 12, fontWeight: '800' },
  demo: { color: colors.red, fontSize: 12, fontWeight: '800' },
  aiNotice: { color: colors.red, fontSize: 13, fontWeight: '700', marginTop: spacing.xs },
  sourceNotice: { color: colors.red, fontSize: 13, fontWeight: '700', marginTop: spacing.xs },
  lessonTitle: { color: colors.text, fontSize: 20, fontWeight: '800', marginTop: spacing.sm },
  meta: { color: colors.textSoft, fontSize: 13, lineHeight: 19, marginTop: spacing.xs },
  cardText: { color: colors.textSoft, lineHeight: 21, marginTop: spacing.sm },
  sectionTitle: { color: colors.text, fontWeight: '800', marginTop: spacing.md },
  question: { paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  button: { backgroundColor: colors.primary, borderRadius: radii.md, padding: spacing.md, alignItems: 'center', marginTop: spacing.md },
  buttonText: { color: colors.white, fontWeight: '700' },
  disabled: { opacity: 0.55 },
  error: { color: colors.red, marginTop: spacing.md },
});
