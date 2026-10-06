import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Plus, Save } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { api } from '../lib/api'
import type { Project, Ruleset } from '../lib/types'
import { Badge, Button, Field, Input, Select, Textarea } from './ui'

const schema = z.object({ function_id: z.string().min(1, 'Select a function'), class_code: z.string().min(1, 'Select a class'), parent_component_id: z.string().optional(), label: z.string().min(1, 'Enter a label'), description: z.string() })
type BuilderValues = z.infer<typeof schema>

export function ManualBuilder({ project, ruleset }: { project: Project; ruleset?: Ruleset }) {
  const queryClient = useQueryClient()
  const [functionNumber, setFunctionNumber] = useState(2)
  const [functionLabel, setFunctionLabel] = useState('Joint 2')
  const form = useForm<BuilderValues>({ resolver: zodResolver(schema), defaultValues: { function_id: project.functions[0]?.id ?? '', class_code: 'M', parent_component_id: '', label: '', description: '' } })
  const values = useWatch({ control: form.control })
  useEffect(() => { if (!form.getValues('function_id') && project.functions[0]) form.setValue('function_id', project.functions[0].id) }, [project.functions, form])
  const validForPreview = Boolean(values.function_id && values.class_code && values.label)
  const payload = { function_id: values.function_id, class_code: values.class_code, parent_component_id: values.parent_component_id || null, label: values.label, description: values.description ?? '' }
  const preview = useQuery({ queryKey: ['preview', project.id, payload], queryFn: () => api.previewComponent(project.id, payload), enabled: validForPreview })
  const create = useMutation({ mutationFn: (body: BuilderValues) => api.createComponent(project.id, { ...body, parent_component_id: body.parent_component_id || null }), onSuccess: async () => { form.reset({ ...form.getValues(), label: '', description: '' }); await queryClient.invalidateQueries({ queryKey: ['project', project.id] }) } })
  const addFunction = useMutation({ mutationFn: () => api.createFunction(project.id, { number: functionNumber, label: functionLabel, description: '' }), onSuccess: async (updated) => { await queryClient.invalidateQueries({ queryKey: ['project', project.id] }); const created = updated.functions.find((item) => item.number === functionNumber); if (created) form.setValue('function_id', created.id) } })
  return <div className="grid h-full grid-cols-[minmax(420px,620px)_1fr] gap-5 overflow-auto p-5">
    <section>
      <div className="mb-5"><p className="section-kicker">Deterministic workflow</p><h2 className="text-xl font-bold text-slate-900">Manual RDS Builder</h2><p className="mt-1 text-sm text-slate-500">Choose structure first. Preview and final designation are compiled by the backend.</p></div>
      {project.functions.length === 0 && <div className="mb-5 border-l-4 border-amber-400 bg-amber-50 p-4"><p className="text-sm font-bold">Create the first function</p><div className="mt-3 grid grid-cols-[100px_1fr_auto] gap-2"><Input aria-label="Function number" type="number" value={functionNumber} onChange={(e) => setFunctionNumber(Number(e.target.value))} /><Input aria-label="Function label" value={functionLabel} onChange={(e) => setFunctionLabel(e.target.value)} /><Button onClick={() => addFunction.mutate()} disabled={!functionLabel || addFunction.isPending}><Plus size={14} />Add</Button></div></div>}
      <form className="grid gap-4" onSubmit={form.handleSubmit((body) => create.mutate(body))}>
        <div className="grid grid-cols-2 gap-4">
          <Field label="1. Assigned function"><Select {...form.register('function_id')}><option value="">Select function…</option>{project.functions.map((item) => <option key={item.id} value={item.id}>=M{item.number} — {item.label}</option>)}</Select></Field>
          <Field label="2. Object class"><Select {...form.register('class_code')}><option value="">Select class…</option>{Object.entries(ruleset?.classes ?? {}).map(([code, item]) => <option key={code} value={code}>{code} — {item.name.replaceAll('_', ' ')}</option>)}</Select></Field>
        </div>
        <Field label="3. Optional containing component"><Select {...form.register('parent_component_id')}><option value="">Independent component</option>{project.components.filter((item) => item.function_id === values.function_id).map((item) => <option key={item.id} value={item.id}>{item.designation} — {item.label}</option>)}</Select></Field>
        <Field label="4. Human label"><Input placeholder="e.g. Servo motor" {...form.register('label')} />{form.formState.errors.label && <span className="text-red-700">{form.formState.errors.label.message}</span>}</Field>
        <Field label="5. Description"><Textarea rows={4} placeholder="Engineering purpose, mounting, or context…" {...form.register('description')} /></Field>
        <div className="border border-purple-200 bg-purple-50 p-4">
          <div className="flex items-center justify-between"><span className="text-xs font-bold uppercase tracking-wider text-purple-800">Live compiler preview</span>{preview.data && <Badge tone={preview.data.valid ? 'success' : 'danger'}>{preview.data.valid ? 'Valid' : 'Invalid'}</Badge>}</div>
          <div data-testid="designation-preview" className="mt-3 font-mono text-2xl font-bold text-purple-950">{validForPreview ? preview.data?.designation || 'Compiling…' : '—'}</div>
          <p className="mt-2 text-xs text-purple-700">This is derived data. The component UUID remains its permanent identity.</p>
        </div>
        {create.error && <p role="alert" className="border border-red-200 bg-red-50 p-2 text-sm text-red-800">{create.error.message}</p>}
        <div className="flex items-center justify-between"><span className="text-xs text-slate-500"><CheckCircle2 className="mr-1 inline" size={14} />Server validation runs before commit</span><Button disabled={!preview.data?.valid || create.isPending}><Save size={14} />Save component</Button></div>
      </form>
    </section>
    <aside className="border-l border-slate-200 pl-5"><p className="section-kicker">Active ruleset</p><h3 className="font-bold">{ruleset?.name}</h3><p className="mt-1 text-xs text-slate-500">Version {ruleset?.version}</p><div className="mt-5 grid gap-2">{Object.entries(ruleset?.classes ?? {}).map(([code, item]) => <div key={code} className="grid grid-cols-[28px_1fr] border-b border-slate-100 py-2 text-xs"><strong className="font-mono text-purple-700">{code}</strong><span><b>{item.name.replaceAll('_', ' ')}</b><br/><span className="text-slate-500">{item.aliases.slice(0, 4).join(', ')}</span></span></div>)}</div></aside>
  </div>
}
