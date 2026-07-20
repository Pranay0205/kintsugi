import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Loading03Icon,
  AlertCircleIcon,
  Settings02Icon,
  Delete02Icon,
  Add01Icon,
  CheckmarkCircle01Icon,
  Edit02Icon,
  ViewIcon,
  AiBrain01Icon,
} from 'hugeicons-react'
import { api, KCDef, PromptComponent, DisambiguationRule } from '../api'

// ---------------------------------------------------------------------------
// Knowledge Components table — rename / edit / delete / add
// ---------------------------------------------------------------------------

function KCRow({ kc }: { kc: KCDef }) {
  const qc = useQueryClient()
  const [name, setName] = useState(kc.name)
  const [kind, setKind] = useState(kc.kind)
  const [category, setCategory] = useState(kc.category)
  const [gapSignal, setGapSignal] = useState(kc.gap_signal)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const dirty = name !== kc.name || kind !== kc.kind || category !== kc.category || gapSignal !== kc.gap_signal

  const save = useMutation({
    mutationFn: () => api.updateKC(kc.name, { name, kind, category, gap_signal: gapSignal }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kcs'] }),
  })

  const remove = useMutation({
    mutationFn: () => api.deleteKC(kc.name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kcs'] }),
  })

  return (
    <tr className="border-b border-slate-100 align-top">
      <td className="py-2 pr-2">
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          className="w-32 font-mono text-xs text-slate-700 border border-transparent hover:border-slate-200 focus:border-violet-400 rounded px-1.5 py-1 focus:outline-none"
        />
      </td>
      <td className="py-2 pr-2">
        <select
          value={kind}
          onChange={e => setKind(e.target.value as KCDef['kind'])}
          className="text-xs border border-slate-200 rounded px-1.5 py-1 focus:outline-none focus:border-violet-400 bg-white"
        >
          <option value="specific">specific</option>
          <option value="structural">structural</option>
        </select>
      </td>
      <td className="py-2 pr-2">
        <input
          value={category}
          onChange={e => setCategory(e.target.value)}
          className="w-28 text-xs text-slate-600 border border-transparent hover:border-slate-200 focus:border-violet-400 rounded px-1.5 py-1 focus:outline-none"
        />
      </td>
      <td className="py-2 pr-2">
        <textarea
          value={gapSignal}
          onChange={e => setGapSignal(e.target.value)}
          rows={2}
          className="w-full min-w-[22rem] text-xs text-slate-600 leading-relaxed border border-transparent hover:border-slate-200 focus:border-violet-400 rounded px-1.5 py-1 focus:outline-none resize-y"
        />
      </td>
      <td className="py-2 pl-1 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          <button
            disabled={!dirty || save.isPending}
            onClick={() => save.mutate()}
            className={`p-1.5 rounded-md transition-colors ${
              dirty ? 'text-violet-600 hover:bg-violet-50' : 'text-slate-200 cursor-default'
            }`}
            title="Save"
          >
            <CheckmarkCircle01Icon size={15} />
          </button>
          {confirmingDelete ? (
            <>
              <button
                onClick={() => remove.mutate()}
                className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 px-1.5"
              >
                Confirm delete
              </button>
              <button
                onClick={() => setConfirmingDelete(false)}
                className="text-[11px] text-slate-400 hover:text-slate-600"
              >
                cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setConfirmingDelete(true)}
              className="p-1.5 rounded-md text-slate-300 hover:text-rose-600 hover:bg-rose-50 transition-colors"
              title="Delete (removes this KC from all problems and submissions)"
            >
              <Delete02Icon size={15} />
            </button>
          )}
        </div>
      </td>
    </tr>
  )
}

function AddKCRow() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [kind, setKind] = useState<'specific' | 'structural'>('specific')
  const [category, setCategory] = useState('')
  const [gapSignal, setGapSignal] = useState('')

  const create = useMutation({
    mutationFn: () => api.createKC({ name: name.trim(), kind, category, gap_signal: gapSignal }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kcs'] })
      setOpen(false)
      setName(''); setCategory(''); setGapSignal(''); setKind('specific')
    },
  })

  if (!open) {
    return (
      <tr>
        <td colSpan={5} className="pt-3">
          <button
            onClick={() => setOpen(true)}
            className="flex items-center gap-1.5 text-xs font-medium text-violet-600 hover:text-violet-700"
          >
            <Add01Icon size={14} />
            Add KC
          </button>
        </td>
      </tr>
    )
  }

  return (
    <tr className="border-b border-slate-100 align-top bg-violet-50/30">
      <td className="py-2 pr-2">
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="NewKCName"
          className="w-32 font-mono text-xs border border-slate-200 rounded px-1.5 py-1 focus:outline-none focus:border-violet-400"
        />
      </td>
      <td className="py-2 pr-2">
        <select
          value={kind}
          onChange={e => setKind(e.target.value as 'specific' | 'structural')}
          className="text-xs border border-slate-200 rounded px-1.5 py-1 focus:outline-none bg-white"
        >
          <option value="specific">specific</option>
          <option value="structural">structural</option>
        </select>
      </td>
      <td className="py-2 pr-2">
        <input
          value={category}
          onChange={e => setCategory(e.target.value)}
          placeholder="Category"
          className="w-28 text-xs border border-slate-200 rounded px-1.5 py-1 focus:outline-none"
        />
      </td>
      <td className="py-2 pr-2">
        <textarea
          value={gapSignal}
          onChange={e => setGapSignal(e.target.value)}
          placeholder="What a gap looks like in student code…"
          rows={2}
          className="w-full min-w-[22rem] text-xs border border-slate-200 rounded px-1.5 py-1 focus:outline-none resize-y"
        />
      </td>
      <td className="py-2 pl-1 whitespace-nowrap">
        <div className="flex items-center gap-1">
          <button
            disabled={!name.trim() || create.isPending}
            onClick={() => create.mutate()}
            className="text-[11px] font-semibold text-violet-600 hover:text-violet-700 disabled:text-slate-300 px-1.5"
          >
            Save
          </button>
          <button onClick={() => setOpen(false)} className="text-[11px] text-slate-400 hover:text-slate-600">
            cancel
          </button>
        </div>
      </td>
    </tr>
  )
}

function KCTable() {
  const { data, isLoading } = useQuery({ queryKey: ['kcs'], queryFn: api.kcs })

  if (isLoading) return <Loading />

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold">
            <th className="pb-2 pr-2">Name</th>
            <th className="pb-2 pr-2">Kind</th>
            <th className="pb-2 pr-2">Category</th>
            <th className="pb-2 pr-2">Gap signal (what a gap looks like)</th>
            <th className="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map(kc => <KCRow key={kc.name} kc={kc} />)}
          <AddKCRow />
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Prompt components — free-text sections of the V3 diagnosis prompt
// ---------------------------------------------------------------------------

function PromptComponentCard({ component }: { component: PromptComponent }) {
  const qc = useQueryClient()
  const [content, setContent] = useState(component.content)
  const dirty = content !== component.content

  const save = useMutation({
    mutationFn: () => api.updatePromptComponent(component.key, content),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['prompt-components'] }),
  })

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-slate-700">{component.label}</p>
        <button
          disabled={!dirty || save.isPending}
          onClick={() => save.mutate()}
          className={`text-[11px] font-semibold px-2 py-0.5 rounded-full transition-colors ${
            dirty ? 'bg-violet-50 text-violet-700 hover:bg-violet-100' : 'text-slate-300'
          }`}
        >
          {save.isPending ? 'Saving…' : 'Save'}
        </button>
      </div>
      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        rows={Math.max(3, content.split('\n').length)}
        spellCheck={false}
        className="w-full text-[12px] font-mono text-slate-700 leading-relaxed border border-slate-100 rounded-lg p-3 focus:outline-none focus:border-violet-300 resize-y bg-slate-50/50"
      />
    </div>
  )
}

function PromptComponents() {
  const { data, isLoading } = useQuery({ queryKey: ['prompt-components'], queryFn: api.promptComponents })
  if (isLoading) return <Loading />
  return (
    <div className="space-y-3">
      {(data ?? []).map(c => <PromptComponentCard key={c.key} component={c} />)}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Disambiguation rules — ordered list injected between components 6 and 7
// ---------------------------------------------------------------------------

function RuleRow({ rule }: { rule: DisambiguationRule }) {
  const qc = useQueryClient()
  const [text, setText] = useState(rule.rule)
  const dirty = text !== rule.rule

  const save = useMutation({
    mutationFn: () => api.updateRule(rule.id, text),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  })
  const remove = useMutation({
    mutationFn: () => api.deleteRule(rule.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  })

  return (
    <div className="flex items-start gap-2">
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        rows={2}
        className="flex-1 text-xs text-slate-700 leading-relaxed border border-slate-100 rounded-lg p-2.5 focus:outline-none focus:border-violet-300 resize-y bg-slate-50/50"
      />
      <div className="flex flex-col gap-1 pt-1">
        <button
          disabled={!dirty || save.isPending}
          onClick={() => save.mutate()}
          className={`p-1.5 rounded-md transition-colors ${dirty ? 'text-violet-600 hover:bg-violet-50' : 'text-slate-200'}`}
          title="Save"
        >
          <CheckmarkCircle01Icon size={15} />
        </button>
        <button
          onClick={() => remove.mutate()}
          className="p-1.5 rounded-md text-slate-300 hover:text-rose-600 hover:bg-rose-50 transition-colors"
          title="Delete rule"
        >
          <Delete02Icon size={15} />
        </button>
      </div>
    </div>
  )
}

function DisambiguationRules() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['rules'], queryFn: api.disambiguationRules })
  const [newRule, setNewRule] = useState('')

  const create = useMutation({
    mutationFn: () => api.createRule(newRule.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['rules'] })
      setNewRule('')
    },
  })

  if (isLoading) return <Loading />

  return (
    <div className="space-y-2.5">
      {(data ?? []).map(r => <RuleRow key={r.id} rule={r} />)}
      <div className="flex items-start gap-2 pt-1">
        <textarea
          value={newRule}
          onChange={e => setNewRule(e.target.value)}
          placeholder="KC A vs KC B — when to pick which…"
          rows={2}
          className="flex-1 text-xs border border-dashed border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-violet-300 resize-y"
        />
        <button
          disabled={!newRule.trim() || create.isPending}
          onClick={() => create.mutate()}
          className="p-1.5 rounded-md text-violet-600 hover:bg-violet-50 disabled:text-slate-200 transition-colors mt-1"
          title="Add rule"
        >
          <Add01Icon size={15} />
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Full prompt preview
// ---------------------------------------------------------------------------

function PromptPreview() {
  const [open, setOpen] = useState(false)
  const { data, refetch, isFetching } = useQuery({
    queryKey: ['prompt-preview'],
    queryFn: api.promptPreview,
    enabled: false,
  })

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <button
        onClick={() => { setOpen(o => !o); if (!open) refetch() }}
        className="flex items-center gap-2 text-sm font-semibold text-slate-800"
      >
        <ViewIcon size={14} className="text-slate-400" />
        Preview assembled prompt
        {isFetching && <Loading03Icon size={13} className="animate-spin text-violet-500" />}
      </button>
      {open && (
        <pre className="mt-3 bg-slate-900 text-slate-100 text-[11px] leading-relaxed rounded-lg p-4 overflow-x-auto whitespace-pre-wrap font-mono max-h-[32rem] overflow-y-auto">
          {data?.prompt ?? '…'}
        </pre>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

function Loading() {
  return (
    <div className="flex items-center gap-2 text-slate-400 text-sm py-6">
      <Loading03Icon size={16} className="animate-spin text-violet-500" />
      Loading…
    </div>
  )
}

function Section({ title, subtitle, icon, children }: {
  title: string; subtitle: string; icon: React.ReactNode; children: React.ReactNode
}) {
  return (
    <div className="space-y-3">
      <div>
        <p className="text-sm font-semibold text-slate-800 flex items-center gap-2">{icon}{title}</p>
        <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
      </div>
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function PromptEditor() {
  return (
    <div className="p-8 max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <Settings02Icon size={22} className="text-violet-500" />
          Prompt Editor
        </h1>
        <p className="text-sm text-slate-500 mt-1 flex items-center gap-1.5">
          <AlertCircleIcon size={13} className="text-amber-400 flex-shrink-0" />
          Edits here take effect on the next live diagnosis — they change what the model is instructed to look for.
        </p>
      </div>

      <Section
        title="Knowledge Components"
        subtitle="The 18 KCs the model can tag. Renaming updates every problem and submission that references the KC; deleting removes it from them too."
        icon={<Edit02Icon size={14} className="text-slate-400" />}
      >
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
          <KCTable />
        </div>
      </Section>

      <Section
        title="Prompt template"
        subtitle="The fixed sections of the diagnosis prompt, in the order they're assembled. {{placeholders}} are filled in per-submission."
        icon={<AiBrain01Icon size={14} className="text-slate-400" />}
      >
        <PromptComponents />
      </Section>

      <Section
        title="Disambiguation rules"
        subtitle="Injected as a numbered list inside the prompt template, right after the disambiguation intro section above."
        icon={<AiBrain01Icon size={14} className="text-slate-400" />}
      >
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
          <DisambiguationRules />
        </div>
      </Section>

      <PromptPreview />
    </div>
  )
}
