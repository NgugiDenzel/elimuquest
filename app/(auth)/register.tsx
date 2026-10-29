import { Link } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, radii, spacing } from '../../src/theme';
import { useAuthActions } from '../../src/hooks/useAuth';
import { useState } from 'react';
import { router } from 'expo-router';

type FormValues = { full_name: string; email: string; password: string };

export default function RegisterScreen() {
  const { control, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    defaultValues: { full_name: '', email: '', password: '' },
  });
  const { register } = useAuthActions();
  const [serverError, setServerError] = useState('');
  const onSubmit = handleSubmit(async ({ full_name, email, password }) => {
    setServerError('');
    try {
      await register(full_name.trim(), email.trim(), password);
      router.replace('/(tabs)');
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Account creation failed. Please try again.');
    }
  });

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.form}>
      <Text style={styles.title}>Create your account</Text>
      <Controller
        control={control}
        name="full_name"
        rules={{ required: 'Enter your name.', minLength: { value: 2, message: 'Name must have at least 2 characters.' } }}
        render={({ field: { onChange, value } }) => (
          <TextInput placeholder="Full name" style={styles.input} value={value} onChangeText={onChange} autoComplete="name" accessibilityLabel="Full name" />
        )}
      />
      {errors.full_name && <Text style={styles.error}>{errors.full_name.message}</Text>}
      <Controller
        control={control}
        name="email"
        rules={{
          required: 'Enter your email address.',
          pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Enter a valid email address.' },
        }}
        render={({ field: { onChange, value } }) => (
          <TextInput placeholder="Email" style={styles.input} value={value} onChangeText={onChange} autoCapitalize="none" keyboardType="email-address" autoComplete="email" accessibilityLabel="Email" />
        )}
      />
      {errors.email && <Text style={styles.error}>{errors.email.message}</Text>}
      <Controller
        control={control}
        name="password"
        rules={{ required: 'Enter a password.', minLength: { value: 10, message: 'Password must have at least 10 characters.' } }}
        render={({ field: { onChange, value } }) => (
          <TextInput placeholder="Password (10+ characters)" secureTextEntry style={styles.input} value={value} onChangeText={onChange} autoComplete="new-password" accessibilityLabel="Password" />
        )}
      />
      {errors.password && <Text style={styles.error}>{errors.password.message}</Text>}
      {!!serverError && <Text style={styles.error} accessibilityRole="alert">{serverError}</Text>}
      <Pressable style={[styles.button, isSubmitting && styles.disabled]} onPress={() => void onSubmit()} disabled={isSubmitting}>
        {isSubmitting ? <ActivityIndicator color={colors.white} /> : <Text style={styles.buttonText}>Sign up</Text>}
      </Pressable>
      <Link href="/(auth)/login" asChild>
        <Pressable style={styles.linkButton}><Text style={styles.linkButtonText}>Already have an account? Log in</Text></Pressable>
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
    fontSize: 30,
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
  linkButton: { alignItems: 'center', marginTop: spacing.md },
  linkButtonText: { color: colors.primary, fontWeight: '700' },
  error: { color: colors.red, fontSize: 13, marginBottom: spacing.sm },
  disabled: { opacity: 0.65 },
});
