import { useState, useMemo, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Treemap,
} from 'recharts'
import {
  Loading03Icon,
  BookOpen01Icon,
  GridViewIcon,
  LayoutGridIcon,
  ChartLineData01Icon,
  ChartBarLineIcon,

  AlertCircleIcon,
} from 'hugeicons-react'
import { api, KCEntry, KCPersistence, ProblemHardness } from '../api'

// ---------------------------------------------------------------------------
// KC metadata
// ---------------------------------------------------------------------------

const KC_CATEGORY: Record<string, { label: string; fill: string }> = {
  'If/Else':         { label: 'Control Flow', fill: '#7c3aed' },
  'NestedIf':        { label: 'Control Flow', fill: '#7c3aed' },
  'While':           { label: 'Loops',        fill: '#2563eb' },
  'For':             { label: 'Loops',        fill: '#2563eb' },
  'NestedFor':       { label: 'Loops',        fill: '#2563eb' },
  'Math+-*/':        { label: 'Math',         fill: '#059669' },
  'Math%':           { label: 'Math',         fill: '#059669' },
  'LogicAndNotOr':   { label: 'Logic',        fill: '#d97706' },
  'LogicCompareNum': { label: 'Logic',        fill: '#d97706' },
  'LogicBoolean':    { label: 'Logic',        fill: '#d97706' },
  'StringFormat':    { label: 'Strings',      fill: '#0891b2' },
  'StringConcat':    { label: 'Strings',      fill: '#0891b2' },
  'StringIndex':     { label: 'Strings',      fill: '#0891b2' },
  'StringLen':       { label: 'Strings',      fill: '#0891b2' },
  'StringEqual':     { label: 'Strings',      fill: '#0891b2' },
  'CharEqual':       { label: 'Strings',      fill: '#0891b2' },
  'ArrayIndex':      { label: 'Arrays',       fill: '#db2777' },
  'DefFunction':     { label: 'Functions',    fill: '#65a30d' },
}

const CATEGORY_ORDER = ['Control Flow', 'Loops', 'Logic', 'Math', 'Strings', 'Arrays', 'Functions']
const ALL_KC_ORDER = [
  'If/Else', 'NestedIf', 'While', 'For', 'NestedFor',
  'Math+-*/', 'Math%', 'LogicAndNotOr', 'LogicCompareNum', 'LogicBoolean',
  'StringFormat', 'StringConcat', 'StringIndex', 'StringLen', 'StringEqual', 'CharEqual',
  'ArrayIndex', 'DefFunction',
]

// ---------------------------------------------------------------------------
// Shared UI primitives
// ---------------------------------------------------------------------------

function Loading() {
  return (
    <div className="flex items-center gap-2 text-slate-400 text-sm py-6">
      <Loading03Icon size={16} className="animate-spin text-violet-500" />
      Loading…
    </div>
  )
}

function Panel({ title, subtitle, icon, children, className = '' }: {
  title: string; subtitle?: string; icon?: React.ReactNode; children: React.ReactNode; className?: string
}) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col ${className}`}>
      <div className="mb-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          {icon}
          <p className="text-sm font-semibold text-slate-800">{title}</p>
        </div>
        {subtitle && <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{subtitle}</p>}
      </div>
      <div className="flex-1 min-h-0">{children}</div>
    </div>
  )
}

// Category legend pills
function CategoryLegend() {
  const cats = useMemo(() =>
    CATEGORY_ORDER.map(label => {
      const entry = Object.values(KC_CATEGORY).find(v => v.label === label)
      return { label, fill: entry?.fill ?? '#94a3b8' }
    }), []
  )
  return (
    <div className="flex flex-wrap gap-2.5 mb-3">
      {cats.map(({ label, fill }) => (
        <span key={label} className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: fill }} />
          {label}
        </span>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Treemap with hover tooltip
// ---------------------------------------------------------------------------

interface HoverNode { name: string; gap_count: number; category: string; x: number; y: number }

function GapTreemap({ entries }: { entries: KCEntry[] }) {
  const [hovered, setHovered] = useState<HoverNode | null>(null)

  const data = useMemo(() => entries.map(e => ({
    name: e.kc,
    gap_count: e.gap_count,
    size: e.gap_count,
  })), [entries])

  const TreemapTile = useCallback((props: any) => {
    const { x, y, width, height, name } = props
    if (!name || width < 4 || height < 4) return null
    const fill = KC_CATEGORY[name]?.fill ?? '#94a3b8'
    const gap_count = props.gap_count ?? data.find(d => d.name === name)?.gap_count ?? 0
    const labelFits = width > 52 && height > 28

    return (
      <g
        onMouseEnter={e => setHovered({ name, gap_count, category: KC_CATEGORY[name]?.label ?? '', x: e.clientX, y: e.clientY })}
        onMouseMove={e => setHovered(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : null)}
        onMouseLeave={() => setHovered(null)}
        style={{ cursor: 'default' }}
      >
        <rect
          x={x + 1} y={y + 1} width={width - 2} height={height - 2}
          fill={fill} fillOpacity={hovered?.name === name ? 1 : 0.82} rx={5}
          style={{ transition: 'fill-opacity 0.15s' }}
        />
        {labelFits && (
          <>
            <text x={x + 7} y={y + 17} fill="white" fontSize={11}
              fontFamily="JetBrains Mono, monospace" fontWeight={600} style={{ pointerEvents: 'none' }}>
              {name}
            </text>
            {height > 44 && (
              <text x={x + 7} y={y + 30} fill="white" fillOpacity={0.72} fontSize={10}
                style={{ pointerEvents: 'none' }}>
                {gap_count} gap{gap_count !== 1 ? 's' : ''}
              </text>
            )}
          </>
        )}
      </g>
    )
  }, [data, hovered?.name])

  return (
    <div className="relative">
      <CategoryLegend />
      <ResponsiveContainer width="100%" height={300}>
        <Treemap data={data} dataKey="size" content={<TreemapTile />} />
      </ResponsiveContainer>

      {hovered && (
        <div
          style={{ position: 'fixed', left: hovered.x + 14, top: hovered.y - 52, zIndex: 50, pointerEvents: 'none' }}
          className="bg-slate-900 text-white px-3 py-2.5 rounded-xl shadow-2xl text-xs space-y-1 border border-slate-700"
        >
          <p className="font-mono font-semibold text-white">{hovered.name}</p>
          <p className="text-slate-400">{hovered.category}</p>
          <p className="text-slate-200">{hovered.gap_count} total gap flag{hovered.gap_count !== 1 ? 's' : ''}</p>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Student × KC matrix — sorted by total gaps, clickable rows
// ---------------------------------------------------------------------------

function StudentKCMatrix() {
  const navigate = useNavigate()
  const [hoveredCell, setHoveredCell] = useState<{ sid: number; kc: string; count: number } | null>(null)

  const { data: matrix, isLoading } = useQuery({
    queryKey: ['class-matrix'],
    queryFn: api.classMatrix,
  })

  if (isLoading) return <Loading />
  if (!matrix?.length) return null

  const lookup = new Map<string, number>()
  matrix.forEach(c => lookup.set(`${c.student_id}::${c.kc}`, c.gap_count))

  // Sort students by total gap count descending
  const studentTotals = new Map<number, number>()
  matrix.forEach(c => studentTotals.set(c.student_id, (studentTotals.get(c.student_id) ?? 0) + c.gap_count))
  const students = [...studentTotals.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([sid]) => sid)

  const maxCount = Math.max(...matrix.map(c => c.gap_count), 1)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-4 text-xs text-slate-400 flex-shrink-0">
        <span className="w-4 h-4 rounded-sm bg-slate-100 inline-block" /> no gaps
        <span className="w-4 h-4 rounded-sm inline-block" style={{ background: '#7c3aed', opacity: 0.3 }} /> few
        <span className="w-4 h-4 rounded-sm inline-block" style={{ background: '#7c3aed', opacity: 0.7 }} /> moderate
        <span className="w-4 h-4 rounded-sm" style={{ background: '#7c3aed' }} /> many
        <span className="text-slate-300 mx-1">·</span>
        color = category · click row → student profile
      </div>
      <div className="overflow-x-auto flex-1">
        <table className="border-collapse text-xs mx-auto">
          <thead>
            <tr>
              <th className="pr-4 pb-2 text-left text-slate-500 font-semibold text-xs w-20">Student</th>
              <th className="pr-4 pb-2 text-right text-slate-500 font-semibold text-xs w-10">Total</th>
              {ALL_KC_ORDER.map(kc => (
                <th key={kc} className="pb-2 text-slate-400 font-normal align-bottom"
                  style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)', height: 110, verticalAlign: 'bottom', paddingBottom: 4, fontSize: 12 }}>
                  <span className="font-mono font-medium" style={{ color: KC_CATEGORY[kc]?.fill ?? '#94a3b8' }}>{kc}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {students.map((sid, rowIdx) => {
              const total = studentTotals.get(sid) ?? 0
              return (
                <tr
                  key={sid}
                  className="cursor-pointer group"
                  onClick={() => navigate(`/student/${sid}`)}
                >
                  <td className="pr-4 py-1 font-mono text-slate-600 whitespace-nowrap text-xs group-hover:text-violet-600 transition-colors">
                    {sid}
                  </td>
                  <td className="pr-4 py-1 text-right font-mono font-bold text-xs"
                    style={{ color: total > 15 ? '#e11d48' : total > 8 ? '#f97316' : '#94a3b8' }}>
                    {total}
                  </td>
                  {ALL_KC_ORDER.map(kc => {
                    const count = lookup.get(`${sid}::${kc}`) ?? 0
                    const fill = KC_CATEGORY[kc]?.fill ?? '#7c3aed'
                    const opacity = count > 0 ? 0.18 + (count / maxCount) * 0.82 : 1
                    const isHovered = hoveredCell?.sid === sid && hoveredCell?.kc === kc
                    return (
                      <td key={kc} className="px-0.5 py-0.5">
                        <div
                          className="w-6 h-6 rounded-sm flex items-center justify-center text-[11px] font-bold transition-all"
                          style={{
                            backgroundColor: count > 0 ? fill : '#f1f5f9',
                            opacity: count > 0 ? opacity : 1,
                            color: count > 0 ? 'white' : 'transparent',
                            outline: isHovered ? `2px solid ${fill}` : 'none',
                            outlineOffset: 1,
                          }}
                          onMouseEnter={() => count > 0 && setHoveredCell({ sid, kc, count })}
                          onMouseLeave={() => setHoveredCell(null)}
                          title={count > 0 ? `Student ${sid} · ${kc}: ${count} flags` : undefined}
                        >
                          {count > 0 ? count : ''}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// KC Persistence
// ---------------------------------------------------------------------------

const PersistTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload as KCPersistence & { pct: number }
  return (
    <div className="bg-slate-900 text-white px-3 py-2.5 rounded-xl shadow-2xl text-xs space-y-1 border border-slate-700">
      <p className="font-mono font-semibold">{d.kc}</p>
      <p className="text-slate-300">{d.still_late} of {d.total_flagged} students still flagged in 2nd half</p>
      <p className={d.pct >= 70 ? 'text-rose-400' : d.pct >= 40 ? 'text-orange-400' : 'text-emerald-400'}>
        {d.pct}% persistence
      </p>
    </div>
  )
}

function PersistenceChart({ data }: { data: KCPersistence[] }) {
  const chartData = data.map(d => ({
    ...d,
    pct: Math.round(d.persistence * 100),
    color: d.persistence >= 0.7 ? '#e11d48' : d.persistence >= 0.4 ? '#f97316' : '#10b981',
  }))

  return (
    <>
      <div className="flex gap-4 text-[11px] text-slate-400 mb-3 flex-shrink-0">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-rose-500 inline-block" />≥70% — re-teach</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-orange-500 inline-block" />40–70%</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-emerald-500 inline-block" />self-correcting</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 36, top: 0, bottom: 0 }}>
          <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`}
            tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="kc" width={108}
            tick={{ fontSize: 10, fill: '#475569', fontFamily: 'JetBrains Mono, monospace' }}
            axisLine={false} tickLine={false} />
          <Tooltip content={<PersistTooltip />} cursor={{ fill: '#f8fafc' }} />
          <Bar dataKey="pct" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {chartData.map((d, i) => <Cell key={i} fill={d.color} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </>
  )
}

// ---------------------------------------------------------------------------
// Problem hardness
// ---------------------------------------------------------------------------

const ProblemTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload as ProblemHardness
  return (
    <div className="bg-slate-900 text-white px-3 py-2.5 rounded-xl shadow-2xl text-xs space-y-1 border border-slate-700">
      <p className="font-mono font-semibold">Problem {d.problem_id}</p>
      <p className="text-slate-400">Assignment {d.assignment_id}</p>
      <p className="text-slate-200">{d.flagged_students} students flagged · {d.total_gaps} total gaps</p>
    </div>
  )
}

function ProblemHardnessChart({ data }: { data: ProblemHardness[] }) {
  const top = data.slice(0, 15)
  return (
    <ResponsiveContainer width="100%" height={290}>
      <BarChart data={top} margin={{ left: 4, right: 16, top: 4, bottom: 28 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="problem_id"
          tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}
          axisLine={false} tickLine={false}
          label={{ value: 'Problem ID', position: 'insideBottom', offset: -18, fontSize: 10, fill: '#94a3b8' }}
        />
        <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}
          label={{ value: 'Students flagged', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10, fill: '#94a3b8' }}
        />
        <Tooltip content={<ProblemTooltip />} cursor={{ fill: '#f8fafc' }} />
        <Bar dataKey="flagged_students" fill="#7c3aed" fillOpacity={0.8} radius={[4, 4, 0, 0]} maxBarSize={28}>
          {top.map((d, i) => (
            <Cell key={i} fill="#7c3aed"
              fillOpacity={d.flagged_students >= 8 ? 1 : d.flagged_students >= 5 ? 0.75 : 0.5}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ---------------------------------------------------------------------------
// Root
// ---------------------------------------------------------------------------

export default function ClassMap() {
  const { data, isLoading: classLoading }  = useQuery({ queryKey: ['class'],            queryFn: api.class })
  const { data: problems }                 = useQuery({ queryKey: ['class-problems'],   queryFn: api.classProblems })
  const { data: persistence }              = useQuery({ queryKey: ['class-persistence'], queryFn: api.classPersistence })

  const entries = (data ?? []).filter(e => e.gap_count > 0)
  const all     = data ?? []
  const total   = entries.reduce((s, e) => s + e.gap_count, 0)
  const actNow  = entries.filter(e => e.student_count >= 7).slice(0, 3)

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Class Skill Map</h1>
        <p className="text-slate-500 mt-1 text-sm">
          {entries.length} of {all.length} KCs flagged · {total} total gap instances
        </p>
      </div>

      {/* Reteach action cards */}
      {actNow.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-1.5">
            <BookOpen01Icon size={12} className="text-slate-400" />
            Reteach before moving on
          </p>
          <div className="grid grid-cols-3 gap-4">
            {actNow.map((e, i) => (
              <div key={e.kc} className="bg-white rounded-xl border border-rose-100 p-4 shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <span className="font-mono font-semibold text-slate-900 text-sm">{e.kc}</span>
                  <span className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    i === 0 ? 'bg-rose-100 text-rose-600' : 'bg-orange-100 text-orange-600'
                  }`}>
                    <AlertCircleIcon size={10} />
                    #{i + 1}
                  </span>
                </div>
                <p className="text-2xl font-bold text-rose-600 leading-none">
                  {e.student_count}
                  <span className="text-sm font-normal text-slate-400 ml-1">/ {all.length} students</span>
                </p>
                <p className="text-xs text-slate-400 mt-1.5">{e.gap_count} flags · {e.kind}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top row: Treemap + Matrix */}
      {classLoading ? <Loading /> : (
        <div className="grid grid-cols-2 gap-6">
          <Panel title="Gap distribution" subtitle="Tile area ∝ total flags · hover for details · color = KC category"
            icon={<GridViewIcon size={14} className="text-slate-400" />}>
            <GapTreemap entries={entries} />
          </Panel>
          <Panel title="Student × KC matrix" subtitle="Rows sorted by total gaps · click any row to open student profile"
            icon={<LayoutGridIcon size={14} className="text-slate-400" />}>
            <StudentKCMatrix />
          </Panel>
        </div>
      )}

      {/* Bottom row: Persistence + Problem hardness */}
      <div className="grid grid-cols-2 gap-6">
        {persistence && persistence.length > 0 && (
          <Panel
            title="Gap persistence"
            subtitle="% still flagged in 2nd half of problem sequence — high = needs explicit re-teaching"
            icon={<ChartLineData01Icon size={14} className="text-slate-400" />}
          >
            <PersistenceChart data={persistence} />
          </Panel>
        )}
        {problems && problems.length > 0 && (
          <Panel
            title="Hardest problems"
            subtitle="Problems where the most students had gaps — candidates for extra scaffolding"
            icon={<ChartBarLineIcon size={14} className="text-slate-400" />}
          >
            <ProblemHardnessChart data={problems} />
          </Panel>
        )}
      </div>


    </div>
  )
}
