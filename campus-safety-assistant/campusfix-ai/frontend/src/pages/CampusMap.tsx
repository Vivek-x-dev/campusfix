import { Suspense, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { motion } from 'framer-motion'
import SceneErrorBoundary from '../components/SceneErrorBoundary'

const buildings = [
  { name: 'Engineering', pos: [-3, 0.8, -2], color: '#334155', severity: 0 },
  { name: 'Library', pos: [2.5, 0.8, -3], color: '#475569', severity: 1 },
  { name: 'Science', pos: [0, 0.6, 2], color: '#475569', severity: 0 },
  { name: 'Cafeteria', pos: [-2, 0.4, 3], color: '#334155', severity: 2 },
  { name: 'Admin', pos: [3.5, 0.7, 1], color: '#334155', severity: 0 },
  { name: 'Dorm North', pos: [0, 0.3, -3.5], color: '#475569', severity: 2 },
]

function BuildingMesh({ b }: { b: typeof buildings[0] }) {
  return (
    <mesh position={b.pos as [number, number, number]}>
      <boxGeometry args={[1.8, 1.6, 1.8]} />
      <meshStandardMaterial color={b.severity === 1 ? '#f97316' : b.severity === 2 ? '#eab308' : b.color} roughness={0.7} />
    </mesh>
  )
}

export default function CampusMap() {
  const [selected, setSelected] = useState<typeof buildings[0] | null>(null)

  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12 space-y-8">
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">3D Campus Map</h1>
        <p className="text-slate-400">Low-poly isometric view with real-time incident markers.</p>
      </div>

      <div className="rounded-2xl overflow-hidden border border-white/10 bg-[#0a0a0a] shadow-2xl shadow-black/40 relative h-[600px]">
        <SceneErrorBoundary
          fallback={
            <div className="absolute inset-0 flex items-center justify-center p-8 text-center text-sm text-slate-400">
              3D map unavailable in this browser (WebGL disabled or blocked). Use the building list below instead.
            </div>
          }
        >
          <Canvas camera={{ position: [5, 6, 7], fov: 40 }} gl={{ antialias: true }}>
            <Suspense fallback={null}>
              <ambientLight intensity={0.4} />
              <directionalLight position={[5, 10, 5]} intensity={2} color="#fbbf24" />
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
                <planeGeometry args={[20, 20]} />
                <meshStandardMaterial color="#0f172a" />
              </mesh>
              {buildings.map((b) => (
                <BuildingMesh key={b.name} b={b} />
              ))}
              {buildings.map((b) => (
                <mesh key={b.name + '-marker'} position={[b.pos[0], 0.9, b.pos[2]]} onClick={() => setSelected(b)}>
                  <sphereGeometry args={[0.15]} />
                  <meshStandardMaterial emissive={b.severity > 0 ? '#f97316' : '#22c55e'} emissiveIntensity={1} />
                </mesh>
              ))}
            </Suspense>
            <OrbitControls enablePan={false} />
          </Canvas>
        </SceneErrorBoundary>
        <div className="absolute bottom-4 left-4 bg-[#030303]/90 backdrop-blur-md border border-white/10 rounded-xl p-4 text-xs text-slate-300">
          <div className="font-bold text-white mb-1">Legend</div>
          <div className="flex gap-3"> <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-rose-500" /> Critical</span> <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400" /> High</span> <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Normal</span> </div>
        </div>
      </div>

      <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="grid md:grid-cols-3 gap-4">
        {buildings.map(b => (
          <button key={b.name} onClick={() => setSelected(b)} className={`text-left rounded-xl border p-4 transition-colors ${selected?.name === b.name ? 'border-amber-400 bg-amber-400/10' : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.05]'}`}>
            <div className="font-bold text-white">{b.name}</div>
            <div className="text-xs text-slate-400">{b.severity === 0 ? 'Normal' : b.severity === 1 ? 'Incident Active' : 'Minor Issue'}</div>
          </button>
        ))}
      </motion.div>
    </div>
  )
}
