export interface Incident {
  id: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  location: string
  description: string
  status: 'open' | 'assigned' | 'in-progress' | 'resolved' | 'closed'
  timestamp: string
  imageUrl?: string
  confidence: number
  riskScore: number
  duplicateOf?: string
  department: string
  action: string
}

export const mockIncidents: Incident[] = [
  { id: 'CF-2024-089', category: 'Electrical', severity: 'critical', location: 'Engineering Building - B2/C1', description: 'Exposed live wires in basement electrical room. Risk of electrocution. Immediate isolation required.', status: 'open', timestamp: '2024-09-18T14:32:00Z', confidence: 0.98, riskScore: 9.2, department: 'Facilities', action: 'Isolate circuit, call electrician, barricade area' },
  { id: 'CF-2024-088', category: 'Structural', severity: 'high', location: 'Library - West Wing Roof', description: 'Water infiltration through roof membrane near skylight. Ceiling tiles sagging. Secondary damage to HVAC.', status: 'assigned', timestamp: '2024-09-18T11:15:00Z', confidence: 0.94, riskScore: 7.8, department: 'Facilities', action: 'Temporary tarping, schedule roof repair' },
  { id: 'CF-2024-087', category: 'Fire Safety', severity: 'high', location: 'Science Complex - Lab 204', description: 'Fire extinguisher missing from wall mount. Pressure gauge in red zone. Replacement needed.', status: 'in-progress', timestamp: '2024-09-17T09:45:00Z', confidence: 0.96, riskScore: 8.1, department: 'Safety', action: 'Replace extinguisher, inspect all units in wing' },
  { id: 'CF-2024-086', category: 'Plumbing', severity: 'medium', location: 'Dormitory North - Floor 3', description: 'Slow drain in communal bathroom. Possible blockage from hair/debris buildup.', status: 'resolved', timestamp: '2024-09-16T18:00:00Z', confidence: 0.89, riskScore: 4.2, department: 'Facilities', action: 'Clear drain, treat with enzyme cleaner' },
  { id: 'CF-2024-085', category: 'Environmental', severity: 'low', location: 'Cafeteria - Outdoor Seating', description: 'Broken glass on patio table. Minor cleanup needed.', status: 'closed', timestamp: '2024-09-15T20:10:00Z', confidence: 0.87, riskScore: 2.1, department: 'Custodial', action: 'Sweep and dispose' },
  { id: 'CF-2024-084', category: 'Lighting', severity: 'medium', location: 'Admin Building - Parking Garage', description: 'Fluorescent fixture flickering on level P2. Potential ballast failure.', status: 'assigned', timestamp: '2024-09-14T07:55:00Z', confidence: 0.91, riskScore: 5.3, department: 'Facilities', action: 'Replace ballast and tube' },
]

export const categories = ['Electrical', 'Structural', 'Fire Safety', 'Plumbing', 'Environmental', 'Lighting', 'HVAC', 'Safety', 'Security', 'Access Control']
export const departments = ['Facilities', 'Safety', 'IT', 'Campus Security', 'Custodial', 'Environmental Health']
