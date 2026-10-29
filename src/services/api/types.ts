export type Profile = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  form: string;
  curriculum_system: string;
  curriculum_level: string;
  timezone: string;
  daily_goal_xp: number;
};

export type Subject = {
  id: string;
  name: string;
  code: string;
  description: string;
  accent: string;
  icon: string;
  curriculum_system: string;
  curriculum_level: string;
  curriculum_version: string;
  curriculum_label: string;
  discipline_group: string | null;
  source_id: string | null;
  progress: number;
  lessons: number;
  ready: boolean;
  next_lesson: string | null;
};

export type LessonQuestion = {
  id: string;
  prompt: string;
  question_type: 'multiple_choice' | 'short_answer';
  options: string[];
};

export type Lesson = {
  id: string;
  title: string;
  description: string;
  content: string;
  topic: string;
  subject: string;
  curriculum_system: string;
  curriculum_level: string;
  curriculum_version: string;
  curriculum_label: string;
  learning_objectives: string[];
  prerequisites: string[];
  explanation_sections: Array<{ title: string; body: string }>;
  worked_examples: Array<{ prompt: string; solution: string; reasoning: string }>;
  source_id: string | null;
  source_reference: string | null;
  questions: LessonQuestion[];
};

export type CurriculumOption = {
  system: string;
  level: string;
  label: string;
  version: string;
  subjects: Array<{
    id: string;
    name: string;
    icon: string;
    discipline_group: string | null;
  }>;
};

export type AdminLesson = {
  id: string;
  title: string;
  topic: string;
  subject: string;
  curriculum_system: string;
  curriculum_level: string;
  curriculum_version: string;
  description: string;
  content: string;
  learning_objectives: string[];
  explanation_sections: Array<{ title: string; body: string }>;
  worked_examples: Array<{ prompt: string; solution: string; reasoning: string }>;
  questions: Array<{
    prompt: string;
    question_type: 'multiple_choice' | 'short_answer';
    options: string[];
    correct_answer: string;
    explanation: string;
    difficulty: string;
  }>;
  published: boolean;
  status: 'draft' | 'in_review' | 'approved' | 'published' | 'archived';
  content_version: number;
  ai_generated: boolean;
  is_demo: boolean;
  source_id: string | null;
  source_reference: string | null;
  author: string | null;
  reviewer: string | null;
  curriculum_alignment?: 'officially_verified' | 'partially_verified' | 'unverified';
  quality_status?: 'validated' | 'needs_review';
};

export type Dashboard = {
  student: Profile;
  total_xp: number;
  league_rank: number | null;
  streak_days: number;
  daily_goal_xp: number;
  daily_progress_xp: number;
  lessons_completed: number;
  accuracy: number;
  subjects: Subject[];
  current_lesson: Lesson | null;
};

export type Progress = {
  total_xp: number;
  lessons_completed: number;
  lessons_attempted: number;
  accuracy: number;
  weekly_activity: Array<{ label: string; xp: number }>;
  mastery: Array<{ subject: string; progress: number; accent: string }>;
  strongest_topics: string[];
  needs_review: string[];
};

export type LeaderboardEntry = {
  rank: number;
  name: string;
  xp: number;
  streak: number;
};

export type AnswerFeedback = {
  question_id: string;
  correct: boolean;
  explanation: string;
};

export type LessonCompletion = {
  session_id: string;
  score_percent: number;
  correct_answers: number;
  total_questions: number;
  xp_awarded: number;
  total_xp: number;
  streak_days: number;
  daily_goal_xp: number;
  daily_progress_xp: number;
  already_completed: boolean;
};
