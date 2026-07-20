import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import {
  Analytics01Icon,
  AlertCircleIcon,
  FlashIcon,
  AiBrain01Icon,
  Settings02Icon,
} from 'hugeicons-react'
import ClassMap from './views/ClassMap'
import TriageList from './views/TriageList'
import StudentProfile from './views/StudentProfile'
import LiveDiagnose from './views/LiveDiagnose'
import PromptEditor from './views/PromptEditor'

const nav = [
  { to: '/',         label: 'Class Skill Map',  Icon: Analytics01Icon },
  { to: '/triage',   label: 'At-Risk Triage',   Icon: AlertCircleIcon  },
  { to: '/diagnose', label: 'Live Diagnosis',    Icon: FlashIcon        },
  { to: '/prompt',   label: 'Prompt Editor',     Icon: Settings02Icon   },
]

export default function App() {
  const navigate = useNavigate()

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-slate-900 flex flex-col border-r border-slate-800">
        <div className="px-5 pt-6 pb-5 border-b border-slate-800 flex items-center gap-3">
          <AiBrain01Icon size={20} className="text-violet-400 flex-shrink-0" />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-0.5">KCDP Dashboard</p>
            <p className="text-sm font-semibold text-white leading-snug">Instructor Tool</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-5 space-y-0.5">
          {nav.map(({ to, label, Icon }) => (
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
                  <Icon size={16} className={`flex-shrink-0 transition-opacity ${isActive ? 'opacity-100' : 'opacity-50'}`} />
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
          <Route path="/prompt"   element={<PromptEditor />} />
        </Routes>
      </main>
    </div>
  )
}
