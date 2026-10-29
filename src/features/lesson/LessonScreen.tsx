import { useLocalSearchParams, router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { QueryState } from '../../components/ui/QueryState';
import { ScreenShell } from '../../components/layout/ScreenShell';
import { api } from '../../services/api/client';
import type { AnswerFeedback, LessonCompletion } from '../../services/api/types';
import { colors, radii, spacing } from '../../theme';

export default function LessonScreen() {
  const { lessonId } = useLocalSearchParams<{ lessonId: string }>();
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [completion, setCompletion] = useState<LessonCompletion | null>(null);
  const startedForLesson = useRef<string | null>(null);

  const lesson = useQuery({
    queryKey: ['lesson', lessonId],
    queryFn: () => api.lesson(lessonId),
    enabled: !!lessonId,
  });
  const startSession = useMutation({
    mutationFn: api.startLesson,
    onSuccess: (result) => setSessionId(result.id),
  });
  const submitAnswer = useMutation({
    mutationFn: (payload: { questionId: string; answer: string }) =>
      api.answer(sessionId!, payload.questionId, payload.answer),
    onSuccess: setFeedback,
  });
  const completeSession = useMutation({
    mutationFn: () => api.completeLesson(sessionId!),
    onSuccess: async (result) => {
      setCompletion(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
        queryClient.invalidateQueries({ queryKey: ['progress'] }),
        queryClient.invalidateQueries({ queryKey: ['leaderboard'] }),
        queryClient.invalidateQueries({ queryKey: ['subjects'] }),
      ]);
    },
  });

  useEffect(() => {
    if (lesson.data && startedForLesson.current !== lesson.data.id) {
      startedForLesson.current = lesson.data.id;
      startSession.mutate(lesson.data.id);
    }
  }, [lesson.data, startSession]);

  if (lesson.isPending || lesson.isError) {
    return (
      <ScreenShell>
        <QueryState loading={lesson.isPending} error={lesson.error?.message} onRetry={() => void lesson.refetch()} />
      </ScreenShell>
    );
  }

  const currentQuestion = lesson.data.questions[questionIndex];
  const beginAgain = () => {
    setCompletion(null);
    setSessionId(null);
    setQuestionIndex(0);
    setAnswer(null);
    setFeedback(null);
    submitAnswer.reset();
    completeSession.reset();
    startSession.reset();
    startSession.mutate(lesson.data.id);
  };

  if (startSession.isError) {
    return (
      <ScreenShell>
        <QueryState error={startSession.error.message} onRetry={beginAgain} />
      </ScreenShell>
    );
  }
  if (startSession.isPending || !sessionId) {
    return (
      <ScreenShell>
        <QueryState loading />
      </ScreenShell>
    );
  }
  if (completion) {
    return (
      <ScreenShell>
        <View style={styles.container}>
          <Text style={styles.eyebrow}>Lesson complete</Text>
          <Text style={styles.title}>{lesson.data.title}</Text>
          <View style={styles.card}>
            <Text style={styles.score}>{completion.score_percent}%</Text>
            <Text style={styles.cardText}>{completion.correct_answers} of {completion.total_questions} answers correct</Text>
            <Text style={styles.reward}>+{completion.xp_awarded} XP earned</Text>
            <Text style={styles.cardText}>Daily goal: {completion.daily_progress_xp}/{completion.daily_goal_xp} XP · {completion.streak_days} day streak</Text>
            <Pressable style={styles.button} onPress={beginAgain}>
              <Text style={styles.buttonText}>Try quiz again</Text>
            </Pressable>
            <Pressable style={styles.button} onPress={() => router.replace('/(tabs)')}>
              <Text style={styles.buttonText}>Back to learning</Text>
            </Pressable>
          </View>
        </View>
      </ScreenShell>
    );
  }
  if (!currentQuestion) {
    return (
      <ScreenShell>
        <View style={styles.container}>
          <Text style={styles.title}>{lesson.data.title}</Text>
          <Text style={styles.cardText}>This published lesson has no questions yet.</Text>
        </View>
      </ScreenShell>
    );
  }

  const moveForward = () => {
    setQuestionIndex((index) => index + 1);
    setAnswer(null);
    setFeedback(null);
    submitAnswer.reset();
  };
  const submit = () => {
    if (!answer || !sessionId) return;
    submitAnswer.mutate({ questionId: currentQuestion.id, answer });
  };

  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.eyebrow}>{lesson.data.subject} · {lesson.data.topic}</Text>
        <Text style={styles.curriculum}>{lesson.data.curriculum_label}</Text>
        <Text style={styles.title}>{lesson.data.title}</Text>
        <Text style={styles.cardText}>{lesson.data.content}</Text>
        {lesson.data.learning_objectives.length > 0 && (
          <View style={styles.contentSection}>
            <Text style={styles.contentHeading}>Learning objectives</Text>
            {lesson.data.learning_objectives.map((objective) => (
              <Text key={objective} style={styles.contentText}>- {objective}</Text>
            ))}
          </View>
        )}
        {lesson.data.explanation_sections.map((section) => (
          <View key={section.title} style={styles.contentSection}>
            <Text style={styles.contentHeading}>{section.title}</Text>
            <Text style={styles.contentText}>{section.body}</Text>
          </View>
        ))}
        {lesson.data.worked_examples.map((example, index) => (
          <View key={`${example.prompt}-${index}`} style={styles.contentSection}>
            <Text style={styles.contentHeading}>Worked example</Text>
            <Text style={styles.contentText}>{example.prompt}</Text>
            <Text style={styles.contentText}>{example.solution}</Text>
            <Text style={styles.contentText}>{example.reasoning}</Text>
          </View>
        ))}
        {!!lesson.data.source_reference && (
          <Text style={styles.source}>Curriculum reference: {lesson.data.source_reference}</Text>
        )}
        <View style={styles.questionCard}>
          <Text style={styles.questionCount}>QUESTION {questionIndex + 1} OF {lesson.data.questions.length}</Text>
          <Text style={styles.question}>{currentQuestion.prompt}</Text>
          {currentQuestion.question_type === 'short_answer' ? (
            <TextInput
              accessibilityLabel="Answer"
              editable={!feedback}
              onChangeText={setAnswer}
              placeholder="Type your answer"
              style={styles.answerInput}
              value={answer ?? ''}
            />
          ) : currentQuestion.options.map((option) => {
              const selected = answer === option;
              return (
                <Pressable
                  key={option}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  onPress={() => !feedback && setAnswer(option)}
                  style={[styles.option, selected && styles.selectedOption]}
                  disabled={!!feedback}
                >
                  <Text style={[styles.optionText, selected && styles.selectedOptionText]}>{option}</Text>
                </Pressable>
              );
            })}
          {!!submitAnswer.error && <Text style={styles.error} accessibilityRole="alert">{submitAnswer.error.message}</Text>}
          {feedback && (
            <View style={[styles.feedback, feedback.correct ? styles.correctFeedback : styles.incorrectFeedback]}>
              <Text style={styles.feedbackTitle}>{feedback.correct ? 'That’s correct!' : 'Not quite'}</Text>
              <Text style={styles.feedbackText}>{feedback.explanation}</Text>
            </View>
          )}
          {!feedback ? (
            <Pressable style={[styles.button, (!answer || submitAnswer.isPending) && styles.disabled]} onPress={submit} disabled={!answer || submitAnswer.isPending}>
              <Text style={styles.buttonText}>{submitAnswer.isPending ? 'Checking…' : 'Check answer'}</Text>
            </Pressable>
          ) : questionIndex + 1 < lesson.data.questions.length ? (
            <Pressable style={styles.button} onPress={moveForward}><Text style={styles.buttonText}>Next question</Text></Pressable>
          ) : (
            <Pressable style={[styles.button, completeSession.isPending && styles.disabled]} onPress={() => completeSession.mutate()} disabled={completeSession.isPending}>
              <Text style={styles.buttonText}>{completeSession.isPending ? 'Saving progress…' : 'Complete lesson'}</Text>
            </Pressable>
          )}
          {!!completeSession.error && <Text style={styles.error} accessibilityRole="alert">{completeSession.error.message}</Text>}
        </View>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.xl, width: '100%', maxWidth: 760, alignSelf: 'center' },
  eyebrow: { color: colors.primary, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1, marginBottom: spacing.sm },
  curriculum: { color: colors.textSoft, fontWeight: '700', marginBottom: spacing.sm },
  title: { fontSize: 30, fontWeight: '800', color: colors.text, marginBottom: spacing.lg },
  cardText: { color: colors.textSoft, fontSize: 15, lineHeight: 23, marginBottom: spacing.md },
  questionCard: { backgroundColor: colors.white, borderRadius: radii.xl, borderWidth: 1, borderColor: colors.border, padding: spacing.xl, marginTop: spacing.md },
  card: { backgroundColor: colors.white, borderRadius: radii.xl, borderWidth: 1, borderColor: colors.border, padding: spacing.xl },
  contentSection: { backgroundColor: colors.white, borderRadius: radii.lg, borderWidth: 1, borderColor: colors.border, padding: spacing.lg, marginBottom: spacing.md },
  contentHeading: { color: colors.text, fontSize: 16, fontWeight: '800', marginBottom: spacing.sm },
  contentText: { color: colors.textSoft, lineHeight: 23, marginBottom: spacing.xs },
  source: { color: colors.textSoft, fontSize: 12, marginBottom: spacing.md },
  questionCount: { color: colors.primary, fontSize: 12, fontWeight: '700', marginBottom: spacing.md },
  question: { color: colors.text, fontSize: 20, lineHeight: 28, fontWeight: '700', marginBottom: spacing.md },
  option: { borderWidth: 1, borderColor: colors.border, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.sm, backgroundColor: colors.white },
  answerInput: { borderWidth: 1, borderColor: colors.border, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.sm, color: colors.text, backgroundColor: colors.white },
  selectedOption: { borderColor: colors.primary, backgroundColor: colors.primarySoft },
  optionText: { color: colors.text, fontWeight: '600' },
  selectedOptionText: { color: colors.primary },
  button: { backgroundColor: colors.primary, borderRadius: radii.md, padding: spacing.md, alignItems: 'center', marginTop: spacing.md },
  buttonText: { color: colors.white, fontWeight: '700' },
  disabled: { opacity: 0.55 },
  feedback: { padding: spacing.md, borderRadius: radii.md, marginTop: spacing.md },
  correctFeedback: { backgroundColor: colors.greenSoft },
  incorrectFeedback: { backgroundColor: '#FFF2F2' },
  feedbackTitle: { color: colors.text, fontWeight: '800', marginBottom: 4 },
  feedbackText: { color: colors.textSoft, lineHeight: 21 },
  error: { color: colors.red, marginTop: spacing.sm },
  score: { color: colors.primary, fontSize: 42, fontWeight: '800', textAlign: 'center', marginBottom: spacing.sm },
  reward: { color: colors.green, fontWeight: '800', fontSize: 18, marginVertical: spacing.md },
});
