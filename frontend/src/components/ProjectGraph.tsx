import { useQuery } from '@tanstack/react-query'
import { Background, Controls, MarkerType, MiniMap, ReactFlow, type Edge, type Node } from '@xyflow/react'
import { useMemo } from 'react'
import { api } from '../lib/api'
import { useWorkspace } from '../lib/store'
import { Empty } from './ui'

export function ProjectGraph({ projectId }: { projectId: string }) {
  const selectComponent = useWorkspace((state) => state.selectComponent)
  const result = useQuery({ queryKey: ['graph', projectId], queryFn: () => api.graph(projectId) })
  const nodes = useMemo<Node[]>(() => (result.data?.nodes ?? []).map((item, index) => ({ id: item.id, type: 'default', position: { x: item.type === 'function' ? 40 : 320 + (index % 3) * 240, y: item.type === 'function' ? index * 150 + 30 : Math.floor(index / 3) * 150 + 30 }, data: { label: item.label }, style: item.type === 'function' ? { background: '#FFF7D8', border: '2px solid #F2C94C', borderRadius: 2, fontWeight: 700 } : { background: '#fff', border: '1px solid #5B3FD6', borderRadius: 2 } })), [result.data])
  const edges = useMemo<Edge[]>(() => (result.data?.edges ?? []).map((item) => ({ id: item.id, source: item.source, target: item.target, label: item.label, animated: item.kind === 'semantic', style: { stroke: item.kind === 'semantic' ? '#C83B46' : item.kind === 'containment' ? '#5B3FD6' : '#A09AAE', strokeDasharray: item.kind === 'semantic' ? '5 4' : undefined }, markerEnd: { type: MarkerType.ArrowClosed, color: item.kind === 'semantic' ? '#C83B46' : '#5B3FD6' } })), [result.data])
  if (!nodes.length) return <div className="p-5"><Empty>Create functions and components to visualize the engineering graph.</Empty></div>
  return <div className="h-full"><div className="absolute z-10 m-3 border border-slate-200 bg-white p-2 text-[10px] shadow-sm"><span className="mr-3 text-purple-700">━━ containment/allocation</span><span className="text-red-700">┄┄ semantic relation</span></div><ReactFlow nodes={nodes} edges={edges} fitView onNodeClick={(_, node) => { if (!result.data?.nodes.find((item) => item.id === node.id && item.type === 'function')) selectComponent(node.id) }}><Background color="#E4E1EA" gap={20}/><MiniMap/><Controls/></ReactFlow></div>
}
