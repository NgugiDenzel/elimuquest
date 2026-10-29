import { Link } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { ScreenShell } from '../../src/components/layout/ScreenShell';
import { QueryState } from '../../src/components/ui/QueryState';
import { api } from '../../src/services/api/client';
import { colors, radii, spacing } from '../../src/theme';

export default function PracticeRoute() {
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: api.subjects });
  if (subjects.isPending || subjects.isError) {
    return (
      <ScreenShell>
        <QueryState loading={subjects.isPending} error={subjects.error?.message} onRetry={() => void subjects.refetch()} />
      </ScreenShell>
    );
  }
  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.title}>Practice</Text>
        <Text style={styles.intro}>Choose a subject to revisit its published lessons. Your answers and progress are saved to your account.</Text>
        {subjects.data.length === 0 ? <Text style={styles.text}>No subjects are available yet.</Text> :
          subjects.data.map((subject) => (
            <Link key={subject.id} href={{ pathname: '/(tabs)/subjects/[subjectId]', params: { subjectId: subject.id } }} asChild>
              <Pressable style={styles.card}>
                <Text style={styles.cardTitle}>{subject.icon}  {subject.name}</Text>
                <Text style={styles.text}>{subject.lessons} published lessons · {subject.progress}% mastery</Text>
                <Text style={styles.link}>Explore lessons →</Text>
              </Pressable>
            </Link>
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
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.lg,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 8,
  },
  intro: { color: colors.textSoft, lineHeight: 22, marginBottom: spacing.lg },
  link: { color: colors.primary, fontWeight: '700', marginTop: spacing.md },
  text: {
    color: colors.textSoft,
    fontSize: 14,
    lineHeight: 22,
  },
});
