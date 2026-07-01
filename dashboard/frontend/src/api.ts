const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path)
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

export interface KCEntry {
  kc: string
  kind: 'specific' | 'structural'
  gap_count: number
  student_count: number
}

export interface StudentSummary {
  id: number
  cluster: string
  sub100_count: number
  top_gaps: string[]
  rank_score: number
}

export interface Flag {
  problem_id: number
  score: number
  attempt_order: number
  required_kcs: string[]
  gaps: string[]
  reasoning: string
  code: string
  source: string
}

export interface TrajectoryPoint {
  kc: string
  attempt_order: number
  failed: boolean
}

export interface SubmissionStat {
  attempt_order: number
  score: number
  gap_count: number
}

export interface StudentDetail {
  id: number
  cluster: string
  sub100_count: number
  weak_kcs: string[]
  strong_kcs: string[]
  flags: Flag[]
  trajectory: TrajectoryPoint[]
  timeline: SubmissionStat[]
}

export interface PracticeItem {
  problem_id: number
  assignment_id: number
}

export interface ReteachRecommendation {
  kc: string
  java_topic: string
  why_struggle: string
  reteach_points: string[]
}

export interface ReteachPlan {
  recommendations: ReteachRecommendation[]
  class_summary: string
}

export interface ReteachKCInput {
  kc: string
  flags: number
  student_count: number
  total_students: number
  kind: string
}

export interface ProblemInfo {
  id: number
  assignment_id: number
  requirement: string
  required_kcs: string[]
}

export interface DiagnoseResult {
  reasoning: string
  gaps: string[]
  invalid_kcs: string[]
  parse_status: string
  source: string
}

export interface MatrixCell {
  student_id: number
  kc: string
  gap_count: number
}

export interface ProblemHardness {
  problem_id: number
  assignment_id: number
  flagged_students: number
  total_gaps: number
}

export interface KCPersistence {
  kc: string
  total_flagged: number
  still_late: number
  persistence: number
}

export const api = {
  class: () => get<KCEntry[]>('/class'),
  classMatrix: () => get<MatrixCell[]>('/class/matrix'),
  classProblems: () => get<ProblemHardness[]>('/class/problems'),
  classPersistence: () => get<KCPersistence[]>('/class/persistence'),
  students: () => get<StudentSummary[]>('/students'),
  student: (id: number) => get<StudentDetail>(`/student/${id}`),
  problems: () => get<ProblemInfo[]>('/problems'),
  reteach: (kcs: ReteachKCInput[]) => post<ReteachPlan>('/reteach', { kcs }),
  practice: (kc: string) => get<PracticeItem[]>(`/practice?kc=${encodeURIComponent(kc)}`),
  diagnose: (studentId: number, problemId: number, code: string) =>
    post<DiagnoseResult>('/diagnose', { student_id: studentId, problem_id: problemId, code }),
}
