import { useState } from 'react'
import { Menu, ShieldAlert, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useLocation } from 'react-router-dom'

const navLinks = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Report', path: '/report' },
  { label: 'AI Analysis', path: '/analysis' },
  { label: 'Map', path: '/map' },
  { label: 'Analytics', path: '/analytics' },
]

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#030303]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-amber-400 to-rose-500 shadow-lg shadow-amber-500/20">
            <ShieldAlert className="h-4 w-4 text-[#030303]" />
          </div>
          <span className="text-lg font-bold tracking-tight text-white">CampusFix <span className="text-amber-300">AI</span></span>
        </Link>
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${pathname === link.path ? 'text-amber-300 bg-amber-300/10' : 'text-slate-300 hover:text-white hover:bg-white/5'}`}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden text-white p-2" aria-label="Toggle menu">
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>
      <AnimatePresence>
        {mobileOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="md:hidden overflow-hidden border-t border-white/10 bg-[#030303]/95 backdrop-blur-xl">
            <div className="flex flex-col px-6 py-4 gap-1">
              {navLinks.map(link => (
                <Link key={link.path} to={link.path} onClick={() => setMobileOpen(false)} className={`rounded-md px-3 py-2 text-sm font-medium ${pathname === link.path ? 'text-amber-300 bg-amber-300/10' : 'text-slate-300'}`}>{link.label}</Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
