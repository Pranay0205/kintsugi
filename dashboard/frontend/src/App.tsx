import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import ClassMap from './views/ClassMap'
import TriageList from './views/TriageList'
import StudentProfile from './views/StudentProfile'
import LiveDiagnose from './views/LiveDiagnose'

const nav = [
  { to: '/',         label: 'Class Skill Map',  dot: 'bg-violet-500' },
  { to: '/triage',   label: 'At-Risk Triage',   dot: 'bg-rose-500'   },
  { to: '/diagnose', label: 'Live Diagnosis',    dot: 'bg-emerald-500'},
]

export default function App() {
  const navigate = useNavigate()

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-slate-900 flex flex-col border-r border-slate-800">
        <div className="px-5 pt-6 pb-5 border-b border-slate-800">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-1">KCDP Dashboard</p>
          <p className="text-sm font-semibold text-white leading-snug">Instructor Tool</p>
        </div>

        <nav className="flex-1 px-3 py-5 space-y-0.5">
          {nav.map(({ to, label, dot }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dot} ${isActive ? 'opacity-100' : 'opacity-40'}`} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/"         element={<ClassMap />} />
          <Route path="/triage"   element={<TriageList onSelect={(id) => navigate(`/student/${id}`)} />} />
          <Route path="/student/:id" element={<StudentProfile />} />
          <Route path="/diagnose" element={<LiveDiagnose />} />
        </Routes>
      </main>
    </div>
  )
}
