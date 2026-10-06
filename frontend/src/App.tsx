import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Box, CheckCircle2, ChevronDown, ChevronRight, CircleAlert, Download, FileCode2, FileSpreadsheet, GitBranch, History, ListTree, Plus, Redo2, Search, ShieldCheck, Sparkles, Table2, Undo2, Upload } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from './lib/api'
import { useWorkspace } from './lib/store'
import type { Project } from './lib/types'
import { FlocTable } from './components/FlocTable'
import { InferenceReview } from './components/InferenceReview'
import { Inspector } from './components/Inspector'
import { ManualBuilder } from './components/ManualBuilder'
import { ProjectChooser } from './components/ProjectChooser'
import { ProjectGraph } from './components/ProjectGraph'
import { Badge, Button, Empty, Input, SecondaryButton } from './components/ui'

function NavigationButton({ view, icon, label, count }: { view: ReturnType<typeof useWorkspace.getState>['activeView']; icon: React.ReactNode; label: string; count?: number }) {
  const { activeView, setView } = useWorkspace()
  return <button className={`flex h-9 items-center gap-2 border-r px-4 text-xs font-bold ${activeView === view ? 'border-t-2 border-t-purple-600 bg-white text-purple-800' : 'border-slate-200 bg-slate-100 text-slate-600 hover:bg-slate-50'}`} onClick={() => setView(view)}>{icon}{label}{count !== undefined && <span className="ml-1 text-[10px] text-slate-400">{count}</span>}</button>
}

function LeftRail({ project }: { project: Project }) {
  const { selectedComponentId, selectComponent, search, setSearch } = useWorkspace()
  const [adding, setAdding] = useState(false)
  const [number, setNumber] = useState(Math.max(0, ...project.functions.map((item) => item.number)) + 1)
  const [label, setLabel] = useState('')
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [context, setContext] = useState<{ x: number; y: number; id: string } | null>(null)
  const queryClient = useQueryClient()
  const addFunction = useMutation({ mutationFn: () => api.createFunction(project.id, { number, label }), onSuccess: async () => { setAdding(false); setLabel(''); await queryClient.invalidateQueries({ queryKey: ['project', project.id] }) } })
  const refresh = async () => { await queryClient.invalidateQueries({ queryKey: ['project', project.id] }); await queryClient.invalidateQueries({ queryKey: ['graph', project.id] }) }
  const move = useMutation({ mutationFn: ({ id, parent, functionId }: { id: string; parent: string | null; functionId?: string }) => api.updateComponent(id, { parent_component_id: parent, ...(functionId ? { function_id: functionId } : {}) }), onSuccess: refresh })
  const duplicate = useMutation({ mutationFn: (id: string) => api.duplicateComponent(id), onSuccess: refresh })
  const remove = useMutation({ mutationFn: (id: string) => api.deleteComponent(id), onSuccess: refresh })
  const visible = useMemo(() => project.components.filter((item) => `${item.designation} ${item.label} ${item.description}`.toLowerCase().includes(search.toLowerCase())), [project.components, search])
  return <aside className="left-rail">
    <div className="border-b border-slate-200 p-3"><label className="relative"><Search className="absolute left-2 top-2 text-slate-400" size={14}/><Input className="pl-8" placeholder="Find component…" value={search} onChange={(e) => setSearch(e.target.value)}/></label></div>
    <div className="flex min-h-0 flex-1 flex-col overflow-auto">
      <div className="rail-heading"><span>Functions</span><button aria-label="Add function" onClick={() => setAdding(!adding)}><Plus size={14}/></button></div>
      {adding && <form className="grid grid-cols-[55px_1fr] gap-1 border-b border-slate-200 bg-amber-50 p-2" onSubmit={(e) => { e.preventDefault(); addFunction.mutate() }}><Input type="number" value={number} onChange={(e) => setNumber(Number(e.target.value))}/><Input autoFocus placeholder="Function label" value={label} onChange={(e) => setLabel(e.target.value)}/><Button className="col-span-2" disabled={!label}>Add function</Button></form>}
      {project.functions.map((fn) => <div key={fn.id}><div className="function-row" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); const id = e.dataTransfer.getData('text/component-id'); if (id) move.mutate({ id, parent: null, functionId: fn.id }) }}><span className="font-mono font-bold text-purple-800">=M{fn.number}</span><span className="truncate">{fn.label}</span></div>{visible.filter((item) => item.function_id === fn.id && !item.parent_component_id).map((component) => <ComponentTree key={component.id} component={component} all={visible} selected={selectedComponentId} select={selectComponent} depth={0} collapsed={collapsed} toggle={(id) => setCollapsed((current) => { const next = new Set(current); if (next.has(id)) next.delete(id); else next.add(id); return next })} onMove={(id, parent) => move.mutate({ id, parent })} onContext={(event, id) => { event.preventDefault(); setContext({ x: event.clientX, y: event.clientY, id }) }}/>)}</div>)}
      {!project.functions.length && <p className="p-3 text-xs text-slate-400">No functions yet</p>}
    </div>
    {context && <div className="fixed z-50 w-44 border border-slate-300 bg-white p-1 text-xs shadow-xl" style={{ left: context.x, top: context.y }} onMouseLeave={() => setContext(null)}><button className="menu-item w-full" onClick={() => { const item = project.components.find((value) => value.id === context.id); if (item) void navigator.clipboard.writeText(item.designation); setContext(null) }}>Copy designation</button><button className="menu-item w-full" onClick={() => { duplicate.mutate(context.id); setContext(null) }}>Duplicate component</button><button className="menu-item w-full text-red-700" onClick={() => { remove.mutate(context.id); setContext(null) }}>Delete component</button></div>}
  </aside>
}

function ComponentTree({ component, all, selected, select, depth, collapsed, toggle, onMove, onContext }: { component: Project['components'][number]; all: Project['components']; selected: string | null; select: (id: string) => void; depth: number; collapsed: Set<string>; toggle: (id: string) => void; onMove: (id: string, parent: string) => void; onContext: (event: React.MouseEvent, id: string) => void }) {
  const children = all.filter((item) => item.parent_component_id === component.id)
  return <><button draggable onDragStart={(e) => e.dataTransfer.setData('text/component-id', component.id)} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); e.stopPropagation(); const id = e.dataTransfer.getData('text/component-id'); if (id && id !== component.id) onMove(id, component.id) }} onContextMenu={(e) => onContext(e, component.id)} className={`component-row ${selected === component.id ? 'selected' : ''}`} style={{ paddingLeft: `${8 + depth * 16}px` }} onClick={() => select(component.id)}>{children.length ? <span onClick={(e) => { e.stopPropagation(); toggle(component.id) }}>{collapsed.has(component.id) ? <ChevronRight size={13}/> : <ChevronDown size={13}/>}</span> : <Box size={13}/>}<span className="font-mono font-semibold">{component.designation.replace(/^=M\d+/, '')}</span><span className="truncate text-slate-500">{component.label}</span></button>{!collapsed.has(component.id) && children.map((child) => <ComponentTree key={child.id} component={child} all={all} selected={selected} select={select} depth={depth + 1} collapsed={collapsed} toggle={toggle} onMove={onMove} onContext={onContext}/>)}</>
}

function Workspace({ project }: { project: Project }) {
  const { activeView } = useWorkspace()
  const rulesets = useQuery({ queryKey: ['rulesets'], queryFn: api.rulesets })
  const ruleset = rulesets.data?.find((item) => item.id === project.ruleset_id)
  if (activeView === 'builder') return <ManualBuilder project={project} ruleset={ruleset}/>
  if (activeView === 'floc') return <FlocTable project={project}/>
  if (activeView === 'graph') return <ProjectGraph projectId={project.id}/>
  if (activeView === 'inference') return <InferenceReview project={project} ruleset={ruleset}/>
  if (activeView === 'validation') return <div className="h-full overflow-auto p-5"><p className="section-kicker">Deterministic checks</p><h2 className="text-xl font-bold">Validation</h2><div className="mt-5 grid gap-2">{project.validation.length ? project.validation.map((issue, index) => <button onClick={() => issue.entity_id && useWorkspace.getState().selectComponent(issue.entity_id)} key={`${issue.code}-${index}`} className="grid grid-cols-[100px_1fr] border border-slate-200 bg-white p-3 text-left text-sm hover:border-purple-400"><Badge tone={issue.severity === 'ERROR' ? 'danger' : 'warning'}>{issue.severity}</Badge><div><b>{issue.code}</b><p>{issue.message}</p>{issue.possible_fix && <p className="mt-1 text-xs text-slate-500">Suggested: {issue.possible_fix}</p>}</div></button>) : <Empty><span><CheckCircle2 className="mx-auto mb-2 text-emerald-600"/>No validation issues. The current project graph is valid.</span></Empty>}</div></div>
  return <div className="p-5"><p className="section-kicker">Append-only audit trail</p><h2 className="text-xl font-bold">Revision History</h2><p className="mt-3 text-sm text-slate-500">Select a component and open its History tab in the inspector to review each create, edit, move, delete, restore, or undo event.</p></div>
}

export function App() {
  const { projectId, activeView, setView } = useWorkspace()
  const queryClient = useQueryClient()
  const project = useQuery({ queryKey: ['project', projectId], queryFn: () => api.project(projectId!), enabled: Boolean(projectId), refetchOnWindowFocus: false })
  const health = useQuery({ queryKey: ['health'], queryFn: api.health })
  const validate = useMutation({ mutationFn: () => api.validate(projectId!), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project', projectId] }) })
  const undo = useMutation({ mutationFn: () => api.undo(projectId!), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['project', projectId] }); await queryClient.invalidateQueries({ queryKey: ['graph', projectId] }) } })
  const redo = useMutation({ mutationFn: () => api.redo(projectId!), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['project', projectId] }); await queryClient.invalidateQueries({ queryKey: ['graph', projectId] }) } })
  const importRef = useRef<HTMLInputElement>(null)
  useEffect(() => { const handler = (event: KeyboardEvent) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z' && projectId) { event.preventDefault(); undo.mutate() } if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y' && projectId) { event.preventDefault(); redo.mutate() } if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'n') { event.preventDefault(); setView('builder') } }; window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler) }, [projectId, setView, undo, redo])
  const importFile = async (file: File) => { const data = new FormData(); data.append('file', file); const response = await fetch('/api/projects/import', { method: 'POST', body: data }); if (!response.ok) throw new Error('Import failed'); const imported = await response.json() as Project; useWorkspace.getState().setProject(imported.id); await queryClient.invalidateQueries({ queryKey: ['projects'] }) }
  return <div className="app-shell">
    <header className="topbar"><div className="flex items-center gap-5"><div className="flex items-center gap-2 font-bold tracking-tight"><div className="grid h-8 w-8 place-items-center bg-amber-400 font-mono text-slate-950">AR</div><span>AutoRDS</span></div><ProjectChooser/></div><div className="flex items-center gap-2"><span className="mr-2 flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-400"><span className={`h-2 w-2 ${health.data ? 'bg-emerald-400' : 'bg-red-400'}`}/>Local {health.data ? 'online' : 'offline'}</span>{projectId && <><SecondaryButton className="border-slate-600 bg-slate-800 text-white hover:bg-slate-700" onClick={() => undo.mutate()}><Undo2 size={14}/>Undo</SecondaryButton><SecondaryButton className="border-slate-600 bg-slate-800 text-white hover:bg-slate-700" onClick={() => redo.mutate()}><Redo2 size={14}/>Redo</SecondaryButton><DropdownMenu.Root><DropdownMenu.Trigger asChild><SecondaryButton className="border-slate-600 bg-slate-800 text-white hover:bg-slate-700"><Download size={14}/>Export<ChevronDown size={12}/></SecondaryButton></DropdownMenu.Trigger><DropdownMenu.Portal><DropdownMenu.Content align="end" className="z-50 min-w-48 border border-slate-300 bg-white p-1 text-xs shadow-xl">{[['json', FileCode2], ['csv', Table2], ['xlsx', FileSpreadsheet], ['pdf', FileCode2]].map(([format, Icon]) => <DropdownMenu.Item asChild key={String(format)}><a className="menu-item" href={`/api/projects/${projectId}/export/${format}`}><Icon size={14}/>FLoC {String(format).toUpperCase()}</a></DropdownMenu.Item>)}<DropdownMenu.Separator className="my-1 h-px bg-slate-200"/><DropdownMenu.Item asChild><a className="menu-item" href={`/api/projects/${projectId}/portable`}><Download size={14}/>Portable .autords</a></DropdownMenu.Item><DropdownMenu.Item className="menu-item" onSelect={() => importRef.current?.click()}><Upload size={14}/>Import .autords</DropdownMenu.Item></DropdownMenu.Content></DropdownMenu.Portal></DropdownMenu.Root><input ref={importRef} hidden type="file" accept=".autords" onChange={(e) => e.target.files?.[0] && void importFile(e.target.files[0])}/><Button className="bg-amber-400 text-slate-950 hover:bg-amber-300" onClick={() => validate.mutate()}><ShieldCheck size={14}/>Validate</Button></>}</div></header>
    {!projectId ? <main className="grid flex-1 place-items-center bg-slate-100"><div className="max-w-md border border-slate-300 bg-white p-8 text-center shadow-sm"><div className="mx-auto mb-4 grid h-12 w-12 place-items-center bg-purple-100 text-purple-700"><ListTree/></div><h1 className="text-2xl font-bold">Reference designations, engineered</h1><p className="mt-2 text-sm leading-6 text-slate-500">Create or select a local project to build deterministic, explainable RDS structures.</p></div></main> : project.isLoading ? <main className="grid flex-1 place-items-center">Loading project…</main> : project.error || !project.data ? <main className="grid flex-1 place-items-center text-red-700">{project.error?.message ?? 'Project not found'}</main> : <>
      <div className="workspace"><LeftRail project={project.data}/><main className="relative min-w-0 bg-[#F8F8FA]"><Workspace project={project.data}/></main><Inspector project={project.data} ruleset={undefined}/></div>
      <nav className="bottom-tabs"><NavigationButton view="builder" icon={<Plus size={14}/>} label="Builder"/><NavigationButton view="floc" icon={<Table2 size={14}/>} label="FLoC" count={project.data.components.length}/><NavigationButton view="graph" icon={<GitBranch size={14}/>} label="Graph"/><NavigationButton view="inference" icon={<Sparkles size={14}/>} label="Queries"/><NavigationButton view="validation" icon={<CircleAlert size={14}/>} label="Validation" count={project.data.validation.length}/><NavigationButton view="history" icon={<History size={14}/>} label="Revision History"/><span className="ml-auto flex items-center px-4 text-[10px] text-slate-400">Ruleset {project.data.ruleset_id} · View {activeView}</span></nav>
    </>}
  </div>
}
