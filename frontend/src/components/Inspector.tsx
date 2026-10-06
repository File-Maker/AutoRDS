import * as Tabs from '@radix-ui/react-tabs'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Clipboard, CopyPlus, Link, Save, Trash2, Undo2, X } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'
import { useWorkspace } from '../lib/store'
import type { Project, Ruleset } from '../lib/types'
import { Badge, Button, Field, Input, SecondaryButton, Select, Textarea } from './ui'

export function Inspector({ project, ruleset }: { project: Project; ruleset?: Ruleset }) {
  const { selectedComponentId, selectComponent } = useWorkspace()
  const component = project.components.find((item) => item.id === selectedComponentId)
  const queryClient = useQueryClient()
  const rulesets = useQuery({ queryKey: ['rulesets'], queryFn: api.rulesets })
  const activeRuleset = ruleset ?? rulesets.data?.find((item) => item.id === project.ruleset_id)
  const [form, setForm] = useState({ componentId: component?.id ?? '', label: component?.label ?? '', description: component?.description ?? '', function_id: component?.function_id ?? '', parent_component_id: component?.parent_component_id ?? '', class_code: component?.class_code ?? '' })
  const [relationTarget, setRelationTarget] = useState('')
  const [relationType, setRelationType] = useState('CONNECTED_TO')
  if (component && form.componentId !== component.id) {
    setForm({ componentId: component.id, label: component.label, description: component.description, function_id: component.function_id, parent_component_id: component.parent_component_id ?? '', class_code: component.class_code })
  }
  const history = useQuery({ queryKey: ['history', component?.id], queryFn: () => api.history(component!.id), enabled: Boolean(component) })
  const explanation = useQuery({ queryKey: ['explanation', component?.id], queryFn: () => api.explanation(component!.id), enabled: Boolean(component) })
  const refresh = async () => { await queryClient.invalidateQueries({ queryKey: ['project', project.id] }); await queryClient.invalidateQueries({ queryKey: ['graph', project.id] }); if (component) await queryClient.invalidateQueries({ queryKey: ['history', component.id] }) }
  const update = useMutation({ mutationFn: () => api.updateComponent(component!.id, { label: form.label, description: form.description, function_id: form.function_id, parent_component_id: form.parent_component_id || null, class_code: form.class_code }), onSuccess: refresh })
  const remove = useMutation({ mutationFn: () => api.deleteComponent(component!.id), onSuccess: async () => { selectComponent(null); await refresh() } })
  const duplicate = useMutation({ mutationFn: () => api.duplicateComponent(component!.id), onSuccess: refresh })
  const addRelation = useMutation({ mutationFn: () => api.createRelation(project.id, { source_component_id: component!.id, target_component_id: relationTarget, relation_type: relationType }), onSuccess: async () => { setRelationTarget(''); await refresh() } })
  const removeRelation = useMutation({ mutationFn: (id: string) => api.deleteRelation(id), onSuccess: refresh })
  const undo = useMutation({ mutationFn: () => api.undo(project.id), onSuccess: refresh })
  if (!component) return <aside className="inspector"><div className="flex items-center justify-between border-b border-slate-200 p-3"><strong className="text-xs uppercase tracking-wider">Inspector</strong></div><div className="p-4 text-sm text-slate-500">Select a component in the tree, FLoC, or graph.</div></aside>
  return <aside className="inspector">
    <div className="flex items-start justify-between border-b border-slate-200 p-3"><div><span className="font-mono text-lg font-bold text-purple-800">{component.designation}</span><div className="mt-1"><Badge tone={component.valid ? 'success' : 'danger'}>{component.valid ? 'Valid' : 'Invalid'}</Badge></div></div><button aria-label="Close inspector" onClick={() => selectComponent(null)}><X size={16}/></button></div>
    <Tabs.Root defaultValue="properties" className="flex min-h-0 flex-1 flex-col"><Tabs.List className="grid grid-cols-3 border-b border-slate-200 text-[11px] font-bold uppercase"><Tabs.Trigger className="tab-trigger" value="properties">Properties</Tabs.Trigger><Tabs.Trigger className="tab-trigger" value="explain">Explain</Tabs.Trigger><Tabs.Trigger className="tab-trigger" value="history">History</Tabs.Trigger></Tabs.List>
      <Tabs.Content value="properties" className="grid gap-3 overflow-auto p-3">
        <Field label="Human label"><Input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })}/></Field>
        <Field label="Description"><Textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}/></Field>
        <Field label="Function"><Select value={form.function_id} onChange={(e) => setForm({ ...form, function_id: e.target.value })}>{project.functions.map((item) => <option value={item.id} key={item.id}>=M{item.number} — {item.label}</option>)}</Select></Field>
        <Field label="Class"><Select value={form.class_code} onChange={(e) => setForm({ ...form, class_code: e.target.value })}>{Object.entries(activeRuleset?.classes ?? {}).map(([code, item]) => <option key={code} value={code}>{code} — {item.name.replaceAll('_', ' ')}</option>)}</Select></Field>
        <Field label="Allocated number"><Input readOnly value={component.allocated_number}/></Field>
        <Field label="Parent"><Select value={form.parent_component_id} onChange={(e) => setForm({ ...form, parent_component_id: e.target.value })}><option value="">Independent</option>{project.components.filter((item) => item.id !== component.id && item.function_id === form.function_id).map((item) => <option value={item.id} key={item.id}>{item.designation} — {item.label}</option>)}</Select></Field>
        <div><span className="field-label">Semantic relations</span>{project.relations.filter((item) => item.source_component_id === component.id || item.target_component_id === component.id).map((item) => <div key={item.id} className="mt-1 flex items-center justify-between border border-slate-200 p-2 text-xs"><span>{item.relation_type}</span><button aria-label="Delete relation" onClick={() => removeRelation.mutate(item.id)}><X size={12}/></button></div>)}{!project.relations.some((item) => item.source_component_id === component.id || item.target_component_id === component.id) && <p className="text-xs text-slate-400">No semantic relations</p>}<div className="mt-2 grid gap-1"><Select value={relationType} onChange={(e) => setRelationType(e.target.value)}>{['DRIVES','SENSES','CONTROLS','MOUNTED_ON','LOCATED_AT','CONNECTED_TO','GUIDES','PROTECTS'].map((type) => <option key={type}>{type}</option>)}</Select><Select value={relationTarget} onChange={(e) => setRelationTarget(e.target.value)}><option value="">Target component…</option>{project.components.filter((item) => item.id !== component.id).map((item) => <option key={item.id} value={item.id}>{item.designation} — {item.label}</option>)}</Select><SecondaryButton disabled={!relationTarget} onClick={() => addRelation.mutate()}><Link size={13}/>Add relation</SecondaryButton></div></div>
        {(update.error || remove.error) && <p className="text-xs text-red-700">{(update.error || remove.error)?.message}</p>}
        <div className="grid grid-cols-2 gap-2"><Button onClick={() => update.mutate()} disabled={update.isPending}><Save size={13}/>Save</Button><SecondaryButton onClick={() => navigator.clipboard.writeText(component.designation)}><Clipboard size={13}/>Copy RDS</SecondaryButton><SecondaryButton onClick={() => duplicate.mutate()}><CopyPlus size={13}/>Duplicate</SecondaryButton><SecondaryButton onClick={() => undo.mutate()}><Undo2 size={13}/>Undo</SecondaryButton><SecondaryButton className="col-span-2 border-red-300 text-red-700 hover:bg-red-50" onClick={() => remove.mutate()}><Trash2 size={13}/>Delete</SecondaryButton></div>
      </Tabs.Content>
      <Tabs.Content value="explain" className="overflow-auto p-3"><p className="text-sm leading-6">{explanation.data?.summary}</p><div className="mt-4 grid gap-2">{component.tokens.map((token) => <div key={token.value} className="grid grid-cols-[64px_1fr] border-b border-slate-100 py-2 text-xs"><strong className="font-mono text-purple-700">{token.value}</strong><span>{token.meaning}</span></div>)}</div>{component.issues.map((issue) => <div key={issue.code} className="mt-3 border-l-4 border-red-400 bg-red-50 p-2 text-xs"><b>{issue.code}</b><p>{issue.message}</p></div>)}</Tabs.Content>
      <Tabs.Content value="history" className="overflow-auto p-3">{history.data?.map((item) => <div key={String(item.id)} className="border-b border-slate-200 py-3 text-xs"><div className="flex justify-between"><b className="uppercase text-purple-700">{String(item.operation)}</b><span className="text-slate-400">{new Date(String(item.timestamp)).toLocaleString()}</span></div><p className="mt-1 text-slate-600">{String(item.reason)}</p></div>)}</Tabs.Content>
    </Tabs.Root>
  </aside>
}
