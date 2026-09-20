import { motion } from 'framer-motion'
import { ArrowDown, ShieldCheck, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import CanvasScene from '../components/CanvasScene'

export default function Landing() {
  return (
    <section className="relative overflow-hidden min-h-[92vh] flex items-center">
      <div className="absolute inset-0 z-0">
        <CanvasScene />
        <div className="absolute inset-0 bg-gradient-to-b from-[#030303]/60 via-[#030303]/40 to-[#030303]" />
      </div>
      <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8 pt-24 pb-16">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease: 'easeOut' }} className="max-w-3xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-xs font-semibold tracking-wide uppercase text-amber-300">
            <Zap className="h-3.5 w-3.5" /> AI Operations Command Center
          </div>
          <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight leading-[1.05] text-white mb-6">
            Detect. Assess.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-rose-300 to-amber-300">Resolve.</span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-300 leading-relaxed mb-10 max-w-2xl">
            CampusFix AI transforms scattered campus reports into structured, visual triage. Vision analysis, duplicate suppression, and automated risk assessment — in one intelligent pipeline.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-lg bg-amber-400 px-6 py-3.5 text-base font-bold text-[#030303] shadow-lg shadow-amber-400/20 hover:bg-amber-300 transition-colors">Open Dashboard <ArrowDown className="h-4 w-4 rotate-[-90deg]" /></Link>
            <Link to="/report" className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-6 py-3.5 text-base font-medium text-white hover:bg-white/10 transition-colors backdrop-blur-sm">Report Incident <ShieldCheck className="h-4 w-4" /></Link>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
