import { useQuery } from '@tanstack/react-query';
import { StyleSheet, Text, View } from 'react-native';
import { ScreenShell } from '../../src/components/layout/ScreenShell';
import { QueryState } from '../../src/components/ui/QueryState';
import { api } from '../../src/services/api/client';
import { colors, spacing } from '../../src/theme';

export default function LeaderboardRoute() {
  const leaderboard = useQuery({ queryKey: ['leaderboard'], queryFn: api.leaderboard });
  if (leaderboard.isPending || leaderboard.isError) {
    return (
      <ScreenShell>
        <QueryState loading={leaderboard.isPending} error={leaderboard.error?.message} onRetry={() => void leaderboard.refetch()} />
      </ScreenShell>
    );
  }
  return (
    <ScreenShell>
      <View style={styles.container}>
        <Text style={styles.title}>League</Text>
        <Text style={styles.subtitle}>Learn consistently and climb the weekly rankings.</Text>
        {leaderboard.data.length === 0 ? <Text style={styles.empty}>Be the first learner on the leaderboard.</Text> :
          leaderboard.data.map((player) => (
            <View key={`${player.rank}-${player.name}`} style={styles.row}>
              <Text style={[styles.rank, player.rank <= 3 && styles.topRank]}>#{player.rank}</Text>
              <View style={styles.playerInfo}>
                <Text style={styles.name}>{player.name}</Text>
                <Text style={styles.streak}>{player.streak} day streak</Text>
              </View>
              <Text style={styles.xp}>{player.xp.toLocaleString()} XP</Text>
            </View>
          ))}
        <Text style={styles.privacy}>Only first names and learning XP are shown.</Text>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.xl, width: '100%', maxWidth: 760, alignSelf: 'center' },
  title: { fontSize: 30, fontWeight: '800', color: colors.text },
  subtitle: { color: colors.textSoft, marginTop: 6, marginBottom: spacing.xl },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  rank: { width: 44, fontSize: 16, fontWeight: '700', color: colors.textSoft },
  topRank: { color: colors.primary },
  playerInfo: { flex: 1 },
  name: { fontSize: 17, color: colors.text, fontWeight: '700' },
  streak: { color: colors.textSoft, marginTop: 4, fontSize: 13 },
  xp: { fontWeight: '700', color: colors.text },
  empty: { color: colors.textSoft, marginTop: spacing.xl },
  privacy: { color: colors.textSoft, fontSize: 12, marginTop: spacing.lg },
});
