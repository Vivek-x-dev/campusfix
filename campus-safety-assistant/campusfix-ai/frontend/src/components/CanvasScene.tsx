import { Suspense, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid } from '@react-three/drei'
import * as THREE from 'three'
import SceneErrorBoundary from './SceneErrorBoundary'

function CampusBuildings() {
  const buildings = useMemo(() => [
    { pos: [-4, 0.4, -3], sz: [2, 2.5, 2], color: '#334155' },
    { pos: [3, 0.4, -2], sz: [1.8, 3, 1.8], color: '#475569' },
    { pos: [-2, 0.3, 2.5], sz: [2.2, 2, 2.2], color: '#334155' },
    { pos: [4, 0.2, 3], sz: [1.5, 1.8, 1.5], color: '#475569' },
  ], [])

  return (
    <group>
      {buildings.map((b, i) => (
        <mesh key={i} position={b.pos as [number, number, number]}>
          <boxGeometry args={b.sz as [number, number, number]} />
          <meshStandardMaterial color={b.color} roughness={0.8} metalness={0.1} />
        </mesh>
      ))}
      {/* Roads */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
        <planeGeometry args={[12, 12]} />
        <meshStandardMaterial color="#1e293b" roughness={0.9} />
        <lineSegments>
          <edgesGeometry args={[new THREE.BoxGeometry(12, 12, 0.01)]} />
          <lineBasicMaterial color="#334155" />
        </lineSegments>
      </mesh>
    </group>
  )
}

export default function CanvasScene() {
  return (
    <SceneErrorBoundary
      fallback={<div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-[#0a0a0a] to-amber-950/40" />}
    >
      <Canvas camera={{ position: [6, 5, 8], fov: 45 }} gl={{ antialias: true, alpha: true }}>
        <Suspense fallback={null}>
          <ambientLight intensity={0.4} />
          <hemisphereLight args={['#93c5fd', '#0f172a', 0.5]} />
          <directionalLight position={[10, 10, 5]} intensity={2} color="#fbbf24" />
          <directionalLight position={[-5, 0, -5]} intensity={1} color="#38bdf8" />
          <CampusBuildings />
          <Grid position={[0, 0.05, 0]} args={[10, 10]} cellSize={1} cellThickness={0.5} sectionSize={5} fadeDistance={20} />
        </Suspense>
        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.4} enablePan={false} />
      </Canvas>
    </SceneErrorBoundary>
  )
}
