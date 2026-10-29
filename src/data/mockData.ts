export type Subject = {
  id: string;
  name: string;
  code: string;
  progress: number;
  accent: string;
  icon: string;
  lessons: number;
  nextLesson: string;
};

export const subjects: Subject[] = [
  { id: 'biology', name: 'Biology', code: 'BIO', progress: 72, accent: '#34A853', icon: '🧬', lessons: 18, nextLesson: 'Cell Structure' },
  { id: 'chemistry', name: 'Chemistry', code: 'CHE', progress: 68, accent: '#5C7CFA', icon: '⚗️', lessons: 16, nextLesson: 'Acids & Bases' },
  { id: 'physics', name: 'Physics', code: 'PHY', progress: 60, accent: '#FFB703', icon: '🚀', lessons: 14, nextLesson: 'Motion & Force' },
  { id: 'math', name: 'Mathematics', code: 'MAT', progress: 81, accent: '#F06595', icon: '📐', lessons: 22, nextLesson: 'Algebraic Expressions' },
];

export const monthlyStats = [
  { label: 'M', value: 42 },
  { label: 'T', value: 64 },
  { label: 'W', value: 51 },
  { label: 'T', value: 80 },
  { label: 'F', value: 70 },
  { label: 'S', value: 92 },
  { label: 'S', value: 76 },
];

export const mastery = [
  { subject: 'Biology', progress: 82, color: '#34A853' },
  { subject: 'Chemistry', progress: 63, color: '#5C7CFA' },
  { subject: 'Mathematics', progress: 74, color: '#F06595' },
  { subject: 'Physics', progress: 58, color: '#FFB703' },
];

export const strongTopics = ['Cell organelles', 'Photosynthesis', 'Momentum'];
export const weakTopics = ['Chemical bonding', 'Wave equations', 'Probability'];

export const leaderboard = [
  { name: 'Maya', xp: 1280, streak: 7 },
  { name: 'Alex', xp: 1210, streak: 6 },
  { name: 'Brian', xp: 1150, streak: 5 },
  { name: 'Jane', xp: 1100, streak: 5 },
];
