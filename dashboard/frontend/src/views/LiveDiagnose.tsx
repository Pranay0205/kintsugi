import { useState, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  FlashIcon,
  Loading03Icon,
  FileUploadIcon,
  CheckmarkCircle01Icon,
  AlertCircleIcon,
  Clock01Icon,
  ArrowRight01Icon,
  Alert01Icon,
} from 'hugeicons-react'
import { api, DiagnoseResult, ProblemInfo } from '../api'

interface HistoryItem {
  studentId: number
  problemId: number
  result: DiagnoseResult
  timestamp: string
}

export default function LiveDiagnose() {
  const { data: students } = useQuery({ queryKey: ['students'], queryFn: api.students })
  const { data: problems } = useQuery({ queryKey: ['problems'], queryFn: api.problems })

  const [studentId, setStudentId] = useState<number>(0)
  const [problemId, setProblemId] = useState<string>('')

  const selectedProblem: ProblemInfo | undefined = problems?.find(p => p.id === parseInt(problemId))
  const [code, setCode] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [result, setResult] = useState<DiagnoseResult | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const loadFile = useCallback((file: File) => {
    const reader = new FileReader()
    reader.onload = e => setCode((e.target?.result as string) ?? '')
    reader.readAsText(file)
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) loadFile(file)
  }, [loadFile])

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) loadFile(file)
  }

  const runDiagnosis = async () => {
    if (!studentId || !problemId || !code.trim()) {
      setError('Select a student, enter a problem ID, and provide code.')
      return
    }
    const pid = parseInt(problemId)
    if (isNaN(pid)) { setError('Problem ID must be a number.'); return }
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const res = await api.diagnose(studentId, pid, code)
      setResult(res)
      setHistory(h => [{
        studentId,
        problemId: pid,
        result: res,
        timestamp: new Date().toLocaleTimeString(),
      }, ...h].slice(0, 20))
    } catch (e: any) {
      setError(e.message ?? 'Diagnosis failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <FlashIcon size={22} className="text-emerald-500" />
          Live Diagnosis
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Drop a .java file, pick the student and problem, and see which KCs are flagged instantly.
        </p>
      </div>

      {/* Input form */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
        {/* Student + Problem row */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-1.5">Student</label>
            <select
              value={studentId}
              onChange={e => setStudentId(Number(e.target.value))}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-400 font-mono"
            >
              <option value={0}>Select student…</option>
              {(students ?? []).map(s => (
                <option key={s.id} value={s.id}>{s.id}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-1.5">Problem</label>
            <select
              value={problemId}
              onChange={e => setProblemId(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-400 font-mono"
            >
              <option value="">Select problem…</option>
              {(problems ?? []).map(p => (
                <option key={p.id} value={p.id}>
                  P{p.id} · A{p.assignment_id} · [{p.required_kcs.join(', ')}]
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Problem context */}
        {selectedProblem && (
          <div className="bg-slate-50 rounded-lg border border-slate-200 px-4 py-3 space-y-2">
            <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold">Requirement</p>
            <p className="text-sm text-slate-700 leading-relaxed">{selectedProblem.requirement}</p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {selectedProblem.required_kcs.map(kc => (
                <span key={kc} className="px-2 py-0.5 bg-violet-50 text-violet-700 border border-violet-100 rounded text-xs font-mono">
                  {kc}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Drop zone */}
        <div>
          <label className="block text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-1.5">Student code</label>
          <div
            className={`relative border-2 border-dashed rounded-xl transition-colors ${
              dragging ? 'border-violet-400 bg-violet-50' : 'border-slate-200 bg-slate-50'
            }`}
            onDragOver={e => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <div className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-200/60">
              <button
                onClick={() => fileRef.current?.click()}
                className="flex items-center gap-1.5 text-[11px] font-medium px-3 py-1 bg-white border border-slate-200 rounded-md text-slate-600 hover:border-violet-300 hover:text-violet-700 transition-colors shadow-sm"
              >
                <FileUploadIcon size={12} />
                Open .java file
              </button>
              <span className="text-xs text-slate-400">or drag & drop here</span>
              {code && (
                <span className="ml-auto text-xs text-emerald-600 font-medium">
                  {code.split('\n').length} lines loaded
                </span>
              )}
            </div>
            <textarea
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder="Paste or drop Java code here…"
              rows={12}
              className="w-full bg-transparent font-mono text-[12px] text-slate-800 p-4 resize-none focus:outline-none placeholder-slate-300 leading-relaxed"
              spellCheck={false}
            />
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".java"
            className="hidden"
            onChange={onFileChange}
          />
        </div>

        {/* Error */}
        {error && (
          <p className="text-sm text-rose-600 flex items-center gap-1.5">
            <Alert01Icon size={14} />
            {error}
          </p>
        )}

        {/* Run button */}
        <button
          onClick={runDiagnosis}
          disabled={loading}
          className="w-full py-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-400 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loading03Icon size={16} className="animate-spin" />
              Running DeepSeek V3…
            </>
          ) : (
            <>
              <FlashIcon size={16} />
              Run Diagnosis
              <ArrowRight01Icon size={14} />
            </>
          )}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-white rounded-xl border border-emerald-200 shadow-sm overflow-hidden">
          <div className="bg-emerald-50/60 px-6 py-4 border-b border-emerald-100 flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-800">Diagnosis result</p>
            <span className="text-[10px] font-semibold px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">LIVE</span>
          </div>
          <div className="px-6 py-5 space-y-5">
            {/* Gaps */}
            <div>
              <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
                {result.gaps.length > 0
                  ? <AlertCircleIcon size={12} className="text-rose-500" />
                  : <CheckmarkCircle01Icon size={12} className="text-emerald-500" />}
                Gaps flagged
                {result.gaps.length === 0 && <span className="ml-1 text-emerald-600 normal-case font-normal">none — looks clean</span>}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.gaps.map(kc => (
                  <span key={kc} className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-100 rounded-lg text-xs font-mono font-medium">
                    {kc}
                  </span>
                ))}
                {result.gaps.length === 0 && (
                  <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-lg text-xs font-mono">
                    perfect score
                  </span>
                )}
              </div>
            </div>

            {/* Invalid KCs */}
            {result.invalid_kcs?.length > 0 && (
              <div>
                <p className="text-[11px] uppercase tracking-widest text-amber-500 font-semibold mb-2">Unrecognised tags (ignored)</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.invalid_kcs.map(kc => (
                    <span key={kc} className="px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-100 rounded text-xs font-mono">{kc}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Reasoning */}
            <div>
              <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-2">Reasoning</p>
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{result.reasoning}</p>
            </div>

            {/* Parse status */}
            {result.parse_status !== 'ok' && (
              <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 border border-amber-100">
                Parse status: {result.parse_status}
              </p>
            )}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div>
          <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-3 flex items-center gap-1.5">
            <Clock01Icon size={12} className="text-slate-400" />
            Session history
          </p>
          <div className="space-y-2">
            {history.map((h, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-slate-200 px-5 py-3.5 flex items-center gap-4 shadow-sm"
              >
                <Clock01Icon size={12} className="text-slate-300 flex-shrink-0" />
                <span className="font-mono text-xs text-slate-400">{h.timestamp}</span>
                <span className="font-mono text-sm font-semibold text-slate-700">S{h.studentId}</span>
                <span className="text-xs text-slate-400">P{h.problemId}</span>
                <div className="flex gap-1 flex-wrap">
                  {h.result.gaps.length === 0
                    ? <span className="text-xs text-emerald-600 font-medium">no gaps</span>
                    : h.result.gaps.map(kc => (
                        <span key={kc} className="px-1.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-100 rounded text-[11px] font-mono">
                          {kc}
                        </span>
                      ))
                  }
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
