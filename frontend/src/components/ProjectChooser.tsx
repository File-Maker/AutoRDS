import * as Dialog from '@radix-ui/react-dialog'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FolderPlus, X } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'
import { useWorkspace } from '../lib/store'
import { Button, Field, Input, SecondaryButton, Textarea } from './ui'

export function ProjectChooser() {
  const { projectId, setProject } = useWorkspace()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()
  const projects = useQuery({ queryKey: ['projects'], queryFn: api.projects })
  const create = useMutation({ mutationFn: api.createProject, onSuccess: (project) => { setProject(project.id); setOpen(false); setName(''); setDescription(''); void queryClient.invalidateQueries({ queryKey: ['projects'] }) } })
  return <div className="flex items-center gap-2">
    <select aria-label="Current project" className="h-8 min-w-52 border border-slate-600 bg-slate-900 px-2 text-sm text-white" value={projectId ?? ''} onChange={(event) => setProject(event.target.value || null)}>
      <option value="">Select project…</option>
      {projects.data?.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select>
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild><SecondaryButton className="border-slate-600 bg-slate-800 text-white hover:bg-slate-700"><FolderPlus size={14} />New project</SecondaryButton></Dialog.Trigger>
      <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-40 bg-slate-950/45" /><Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[430px] -translate-x-1/2 -translate-y-1/2 border border-slate-300 bg-white p-5 shadow-xl">
        <div className="mb-5 flex items-start justify-between"><div><Dialog.Title className="text-lg font-bold">Create engineering project</Dialog.Title><Dialog.Description className="mt-1 text-sm text-slate-500">Stored locally using the EE3 2026–2027 ruleset.</Dialog.Description></div><Dialog.Close aria-label="Close"><X size={18} /></Dialog.Close></div>
        <form className="grid gap-4" onSubmit={(event) => { event.preventDefault(); create.mutate({ name, description }) }}>
          <Field label="Project name"><Input autoFocus value={name} onChange={(event) => setName(event.target.value)} /></Field>
          <Field label="Description"><Textarea rows={3} value={description} onChange={(event) => setDescription(event.target.value)} /></Field>
          {create.error && <p className="text-xs text-red-700">{create.error.message}</p>}
          <div className="flex justify-end gap-2"><Dialog.Close asChild><SecondaryButton type="button">Cancel</SecondaryButton></Dialog.Close><Button disabled={!name.trim() || create.isPending}>Create project</Button></div>
        </form>
      </Dialog.Content></Dialog.Portal>
    </Dialog.Root>
  </div>
}
