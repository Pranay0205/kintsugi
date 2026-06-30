import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, StudentSummary } from '../api'

const CLUSTER_STYLE: Record<string, { badge: string; dot: string }> = {
  struggling:   { badge: 'bg-rose-50 text-rose-700 border-rose-100',     dot: 'bg-rose-400'   },
  average:      { badge: 'bg-amber-50 text-amber-700 border-amber-100',   dot: 'bg-amber-400'  },
  high:         { badge: 'bg-emerald-50 text-emerald-700 border-emerald-100', dot: 'bg-emerald-400' },
}

interface Props { onSelect: (id: number) => void }

export default function TriageList({ onSelect }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['students'],
    queryFn: api.students,
  })
  const [filter, setFilter] = useState('')

  if (isLoading) return (
    <div className="p-8 flex items-center gap-2 text-slate-400 text-sm">
      <span className="animate-spin w-4 h-4 border-2 border-slate-300 border-t-violet-500 rounded-full inline-block" />
      Loading…
    </div>
  )
  if (error) return <div className="p-8 text-rose-500 text-sm">Failed to load data.</div>

  const all = data ?? []
  const students = filter ? all.filter(s => s.cluster === filter) : all
  const maxScore = all[0]?.rank_score ?? 1

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">At-Risk Triage</h1>
        <p className="text-slate-500 mt-1 text-sm">Ranked by recurrence-weighted gap score.</p>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Students tracked', value: all.length },
          { label: 'Avg sub-100% count', value: Math.round(all.reduce((s, x) => s + x.sub100_count, 0) / (all.length || 1)) },
          { label: 'Most urgent', value: all[0]?.id ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 shadow-sm px-5 py-4">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">{label}</p>
            <p className="text-2xl font-bold text-slate-900 mt-1 font-mono">{value}</p>
          </div>
        ))}
      </div>

      {/* Filter pills */}
      <div className="flex gap-2">
        {['', 'struggling', 'average', 'high'].map(c => {
          const style = CLUSTER_STYLE[c] ?? {}
          return (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                filter === c
                  ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-violet-300'
              }`}
            >
              {c && <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />}
              {c ? c.charAt(0).toUpperCase() + c.slice(1) : 'All students'}
            </button>
          )
        })}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-[11px] uppercase tracking-widest text-slate-400 bg-slate-50/80">
              <th className="text-left px-5 py-3 font-semibold">Rank</th>
              <th className="text-left px-4 py-3 font-semibold">Student</th>
              <th className="text-left px-4 py-3 font-semibold">Cluster</th>
              <th className="px-4 py-3 font-semibold">
                <span title="Non-perfect submissions — higher = more evidence">Confidence</span>
              </th>
              <th className="text-right px-4 py-3 font-semibold">Risk score</th>
              <th className="text-left px-4 py-3 font-semibold">Top gaps</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {students.map((s, i) => {
              const pct = (s.rank_score / maxScore) * 100
              const clStyle = CLUSTER_STYLE[s.cluster] ?? CLUSTER_STYLE['average']
              return (
                <tr
                  key={s.id}
                  className="hover:bg-slate-50/80 cursor-pointer transition-colors group"
                  onClick={() => onSelect(s.id)}
                >
                  <td className="px-5 py-3.5">
                    <span className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                      i === 0 ? 'bg-rose-100 text-rose-700' :
                      i === 1 ? 'bg-orange-100 text-orange-700' :
                      i === 2 ? 'bg-amber-100 text-amber-700' : 'text-slate-400'
                    }`}>{i + 1}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="font-mono font-semibold text-slate-800">{s.id}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${clStyle.badge}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${clStyle.dot}`} />
                      {s.cluster.charAt(0).toUpperCase() + s.cluster.slice(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2 justify-center">
                      <span className="text-xs font-mono font-semibold text-slate-600">{s.sub100_count}</span>
                      <span className="text-xs text-slate-400">subs</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-violet-500 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="font-mono text-sm font-bold text-violet-700 tabular-nums w-10 text-right">
                        {s.rank_score.toFixed(1)}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex flex-wrap gap-1">
                      {(s.top_gaps ?? []).map(kc => (
                        <span key={kc} className="px-1.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-100 rounded text-[11px] font-mono">
                          {kc}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-slate-300 group-hover:text-violet-400 transition-colors text-right">→</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {students.length === 0 && (
          <div className="py-12 text-center text-slate-400 text-sm">No students match filter.</div>
        )}
      </div>

    </div>
  )
}
