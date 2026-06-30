import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import {
  Loading03Icon,
  AlertCircleIcon,
  ArrowLeft01Icon,
  ArrowUp01Icon,
  ArrowDown01Icon,
  ArrowRight01Icon,
  Mortarboard01Icon,
  FlashIcon,
  CheckmarkCircle01Icon,
  Flag01Icon,
  ChartLineData01Icon,
  GridViewIcon,
} from 'hugeicons-react'
import { Flag, SubmissionStat, TrajectoryPoint } from '../api'
import { api } from '../api'

// ---------------------------------------------------------------------------
// Gap trend chart
// ---------------------------------------------------------------------------

const TrendTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload as SubmissionStat
  return (
    <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-xs space-y-1">
      <p className="text-slate-400">Problem #{d.attempt_order}</p>
      <p>Score: <span className="font-semibold">{(d.score * 100).toFixed(0)}%</span></p>
      <p>Gaps: <span className="font-semibold text-rose-400">{d.gap_count}</span></p>
    </div>
  )
}

function GapTrendChart({ timeline }: { timeline: SubmissionStat[] }) {
  if (!timeline?.length) return null

  // Simple moving average (window 5)
  const smoothed = timeline.map((_, i) => {
    const window = timeline.slice(Math.max(0, i - 2), i + 3)
    return { ...timeline[i], smooth: window.reduce((s, x) => s + x.gap_count, 0) / window.length }
  })

  const half = Math.floor(smoothed.length / 2)
  const firstHalfAvg = smoothed.slice(0, half).reduce((s, x) => s + x.gap_count, 0) / half
  const secondHalfAvg = smoothed.slice(half).reduce((s, x) => s + x.gap_count, 0) / (smoothed.length - half)
  const improving = secondHalfAvg < firstHalfAvg - 0.2

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <ChartLineData01Icon size={14} className="text-slate-400" />
            Gap trend over time
          </p>
          <p className="text-xs text-slate-400 mt-0.5">Gap count per submission in problem sequence</p>
        </div>
        <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border ${
          improving
            ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
            : 'bg-amber-50 text-amber-700 border-amber-100'
        }`}>
          {improving
            ? <><ArrowDown01Icon size={12} /> Improving</>
            : <><ArrowRight01Icon size={12} /> Not improving</>}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={smoothed} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="attempt_order"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            label={{ value: 'Problem sequence', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#94a3b8' }}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            width={24}
          />
          <Tooltip content={<TrendTooltip />} cursor={{ stroke: '#e2e8f0' }} />
          <Area
            type="monotone"
            dataKey="gap_count"
            fill="#fce7f3"
            stroke="#f43f5e"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: '#f43f5e' }}
          />
          <Line
            type="monotone"
            dataKey="smooth"
            stroke="#7c3aed"
            strokeWidth={2}
            dot={false}
            strokeDasharray="4 2"
          />
        </ComposedChart>
      </ResponsiveContainer>
      <div className="flex gap-4 mt-3 text-xs text-slate-400">
        <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-rose-400 inline-block rounded" /> gap count</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-violet-600 inline-block rounded" style={{ borderTop: '2px dashed #7c3aed', background: 'none', height: 0 }} /> 5-point moving avg</span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Trajectory grid
// ---------------------------------------------------------------------------

function Trajectory({ points }: { points: TrajectoryPoint[] }) {
  if (!points?.length) return null
  const kcs = [...new Set(points.map(p => p.kc))].sort()
  const maxOrder = Math.max(...points.map(p => p.attempt_order))
  const lookup = new Set(points.map(p => `${p.kc}::${p.attempt_order}`))

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <p className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <GridViewIcon size={14} className="text-slate-400" />
          KC pattern across submissions
        </p>
      <div className="overflow-x-auto">
        <table className="text-[11px] border-collapse mx-auto">
          <thead>
            <tr>
              <th className="text-left pr-4 pb-1.5 text-slate-400 font-medium w-32">KC</th>
              {Array.from({ length: maxOrder }, (_, i) => (
                <th key={i} className="px-px pb-1.5 text-slate-300 text-center w-4 font-normal">{i + 1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {kcs.map(kc => (
              <tr key={kc}>
                <td className="pr-4 py-px font-mono text-slate-600 whitespace-nowrap">{kc}</td>
                {Array.from({ length: maxOrder }, (_, i) => {
                  const failed = lookup.has(`${kc}::${i + 1}`)
                  return (
                    <td key={i} className="px-px py-px text-center">
                      <span
                        className={`inline-block w-3 h-3 rounded-sm transition-colors ${failed ? 'bg-rose-400' : 'bg-slate-100'}`}
                        title={failed ? `Problem ${i + 1}: gap flagged` : `Problem ${i + 1}: ok`}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[11px] text-slate-400">
        <span className="inline-block w-2.5 h-2.5 rounded-sm bg-rose-400 mr-1.5 align-middle" />
        gap flagged · columns = problem sequence order
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Flag card
// ---------------------------------------------------------------------------

function FlagCard({ flag }: { flag: Flag }) {
  const [open, setOpen] = useState(false)

  return (
    <div className={`rounded-xl border shadow-sm overflow-hidden ${
      flag.source === 'live'
        ? 'border-violet-200 bg-violet-50/30'
        : 'border-slate-200 bg-white'
    }`}>
      <button
        className="w-full text-left px-5 py-3.5 flex items-center gap-3 hover:bg-slate-50/60 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span className="font-mono text-sm font-semibold text-slate-700">P{flag.problem_id}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
          flag.score < 0.5 ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
        }`}>
          {(flag.score * 100).toFixed(0)}%
        </span>
        {flag.source === 'live' && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-100 text-violet-700 font-semibold">LIVE</span>
        )}
        <div className="flex gap-1 flex-wrap">
          {flag.gaps?.map(kc => (
            <span key={kc} className="px-1.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-100 rounded text-[11px] font-mono">
              {kc}
            </span>
          ))}
          {!flag.gaps?.length && <span className="text-xs text-slate-400 italic">no gaps flagged</span>}
        </div>
        <span className="ml-auto text-slate-300">
          {open
            ? <ArrowUp01Icon size={14} />
            : <ArrowDown01Icon size={14} />}
        </span>
      </button>

      {open && (
        <div className="border-t border-slate-100 px-5 py-4 space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1.5">Required KCs</p>
            <div className="flex flex-wrap gap-1.5">
              {flag.required_kcs?.map(kc => (
                <span key={kc} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-mono">{kc}</span>
              ))}
            </div>
          </div>

          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1.5">Reasoning</p>
            {flag.reasoning ? (
              <p className="text-sm text-slate-700 leading-relaxed">{flag.reasoning}</p>
            ) : (
              <p className="text-sm text-slate-400 italic">Reasoning not available for this submission.</p>
            )}
          </div>

          {flag.code && (
            <div>
              <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1.5">Student code</p>
              <pre className="bg-slate-900 text-slate-100 text-[11px] leading-relaxed rounded-lg p-4 overflow-x-auto whitespace-pre-wrap font-mono">
                {flag.code}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// KC chip
// ---------------------------------------------------------------------------

function KCChip({ kc, variant }: { kc: string; variant: 'weak' | 'strong' }) {
  return (
    <span className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium border ${
      variant === 'weak'
        ? 'bg-rose-50 text-rose-700 border-rose-100'
        : 'bg-emerald-50 text-emerald-700 border-emerald-100'
    }`}>
      {kc}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function StudentProfile() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const sid = parseInt(id ?? '0')
  const { data, isLoading, error } = useQuery({
    queryKey: ['student', sid],
    queryFn: () => api.student(sid),
    enabled: !!sid,
  })

  if (isLoading) return (
    <div className="p-8 flex items-center gap-2 text-slate-400 text-sm">
      <Loading03Icon size={16} className="animate-spin text-violet-500" />
      Loading…
    </div>
  )
  if (error) return (
    <div className="p-8 flex items-center gap-2 text-rose-500 text-sm">
      <AlertCircleIcon size={16} />
      Failed to load student {sid}.
    </div>
  )
  if (!data)  return null

  const studyFlags = data.flags?.filter(f => f.source !== 'live') ?? []
  const liveFlags  = data.flags?.filter(f => f.source === 'live') ?? []

  return (
    <div className="p-8 max-w-4xl space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/triage')}
        className="text-sm text-slate-400 hover:text-slate-700 flex items-center gap-1.5 transition-colors"
      >
        <ArrowLeft01Icon size={14} />
        Back to triage
      </button>

      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center">
          <Mortarboard01Icon size={22} className="text-violet-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-mono">Student {data.id}</h1>
          <div className="flex items-center gap-2 mt-0.5 text-sm text-slate-500">
            <span className="capitalize">{data.cluster}</span>
            <span className="text-slate-300">·</span>
            <span><strong className="text-slate-700">{data.sub100_count}</strong> non-perfect submissions</span>
          </div>
        </div>
        <button
          onClick={() => navigate('/diagnose')}
          className="ml-auto flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <FlashIcon size={14} />
          Run live diagnosis
        </button>
      </div>

      {/* KC summary */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: 'Weak KCs',   kcs: data.weak_kcs,   variant: 'weak'   as const, Icon: AlertCircleIcon,      iconClass: 'text-rose-400'    },
          { label: 'Strong KCs', kcs: data.strong_kcs, variant: 'strong' as const, Icon: CheckmarkCircle01Icon, iconClass: 'text-emerald-500' },
        ].map(({ label, kcs, variant, Icon, iconClass }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-3 flex items-center gap-1.5">
              <Icon size={12} className={iconClass} />
              {label}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {kcs?.length
                ? kcs.map(kc => <KCChip key={kc} kc={kc} variant={variant} />)
                : <span className="text-sm text-slate-400">—</span>
              }
            </div>
          </div>
        ))}
      </div>

      {/* Gap trend */}
      {data.timeline?.length > 0 && <GapTrendChart timeline={data.timeline} />}

      {/* Trajectory */}
      {data.trajectory?.length > 0 && <Trajectory points={data.trajectory} />}

      {/* Study flags */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Flag01Icon size={14} className="text-rose-400" />
          Flagged submissions
        </p>
        <div className="space-y-2">
          {studyFlags.length
            ? studyFlags.map((f, i) => <FlagCard key={i} flag={f} />)
            : <p className="text-sm text-slate-400 bg-white rounded-xl border border-slate-200 p-5">No flagged submissions.</p>
          }
        </div>
      </div>

      {/* Live flags */}
      {liveFlags.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <FlashIcon size={14} className="text-violet-500" />
            Live diagnoses
          </p>
          <div className="space-y-2">
            {liveFlags.map((f, i) => <FlagCard key={i} flag={f} />)}
          </div>
        </div>
      )}
    </div>
  )
}
