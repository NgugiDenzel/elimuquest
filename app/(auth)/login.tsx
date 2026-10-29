import { Link } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, radii, spacing } from '../../src/theme';
import { useAuthActions } from '../../src/hooks/useAuth';
import { useState } from 'react';
import { router } from 'expo-router';

type FormValues = { email: string; password: string };

export default function LoginScreen() {
  const { control, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    defaultValues: { email: '', password: '' },
  });
  const { login } = useAuthActions();
  const [serverError, setServerError] = useState('');
  const onSubmit = handleSubmit(async ({ email, password }) => {
    setServerError('');
    try {
      await login(email.trim(), password);
      router.replace('/(tabs)');
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Sign in failed. Please try again.');
    }
  });

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.form}>
      <Text style={styles.title}>Welcome back</Text>
      <Controller
        control={control}
        name="email"
        rules={{
          required: 'Enter your email address.',
          pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Enter a valid email address.' },
        }}
        render={({ field: { onChange, value } }) => (
          <TextInput
            placeholder="Email"
            style={styles.input}
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
            value={value}
            onChangeText={onChange}
            accessibilityLabel="Email"
          />
        )}
      />
      {errors.email && <Text style={styles.error}>{errors.email.message}</Text>}
      <Controller
        control={control}
        name="password"
        rules={{ required: 'Enter your password.' }}
        render={({ field: { onChange, value } }) => (
          <TextInput
            placeholder="Password"
            secureTextEntry
            style={styles.input}
            autoComplete="current-password"
            value={value}
            onChangeText={onChange}
            accessibilityLabel="Password"
          />
        )}
      />
      {errors.password && <Text style={styles.error}>{errors.password.message}</Text>}
      {!!serverError && <Text style={styles.error} accessibilityRole="alert">{serverError}</Text>}
      <Pressable style={[styles.button, isSubmitting && styles.disabled]} onPress={() => void onSubmit()} disabled={isSubmitting}>
        {isSubmitting ? <ActivityIndicator color={colors.white} /> : (
          <Text style={styles.buttonText}>Log in</Text>
        )}
      </Pressable>
      <Link href="/(auth)/register" asChild>
        <Pressable style={styles.linkButton}>
          <Text style={styles.linkButtonText}>Create account</Text>
        </Pressable>
      </Link>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: spacing.xl,
  },
  screen: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  form: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  title: {
    fontSize: 32,
    color: colors.text,
    fontWeight: '800',
    marginBottom: spacing.xl,
  },
  input: {
    backgroundColor: colors.white,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
    fontSize: 16,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: radii.lg,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  buttonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  linkButton: {
    alignItems: 'center',
    marginTop: spacing.md,
  },
  linkButtonText: {
    color: colors.primary,
    fontWeight: '700',
  },
  error: {
    color: colors.red,
    fontSize: 13,
    marginBottom: spacing.sm,
  },
  disabled: {
    opacity: 0.65,
  },
});
