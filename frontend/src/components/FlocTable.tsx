import { flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState, type VisibilityState } from '@tanstack/react-table'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowUpDown, Columns3, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useWorkspace } from '../lib/store'
import { api } from '../lib/api'
import type { Component, Project } from '../lib/types'
import { Badge, Button, Input, Select } from './ui'

export function FlocTable({ project }: { project: Project }) {
  const components = project.components
  const { search, setSearch, selectComponent, selectedComponentId } = useWorkspace()
  const [sorting, setSorting] = useState<SortingState>([{ id: 'designation', desc: false }])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [classFilter, setClassFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [bulkClass, setBulkClass] = useState('')
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(() => JSON.parse(localStorage.getItem('autords-columns') ?? '{}'))
  const queryClient = useQueryClient()
  const data = useMemo(() => components.filter((item) => (!classFilter || item.class_code === classFilter) && (!statusFilter || String(item.valid) === statusFilter)), [components, classFilter, statusFilter])
  const bulk = useMutation({ mutationFn: () => api.bulkComponents(project.id, [...selected], { class_code: bulkClass }), onSuccess: async () => { setSelected(new Set()); await queryClient.invalidateQueries({ queryKey: ['project', project.id] }) } })
  const columns = useMemo<ColumnDef<Component>[]>(() => [
    { accessorKey: 'designation', header: 'RDS', cell: ({ row }) => <span className="font-mono font-bold text-purple-800">{row.original.designation}</span> },
    { accessorKey: 'label', header: 'Component' },
    { id: 'function', accessorFn: (row) => `M${row.function_number}`, header: 'Function' },
    { accessorKey: 'class_code', header: 'Class' },
    { accessorKey: 'parent_label', header: 'Parent', cell: ({ getValue }) => getValue<string>() || '—' },
    { accessorKey: 'description', header: 'Description' },
    { accessorKey: 'valid', header: 'Status', cell: ({ row }) => <Badge tone={row.original.valid ? 'success' : 'danger'}>{row.original.valid ? 'Valid' : 'Invalid'}</Badge> },
    { id: 'warnings', accessorFn: (row) => row.issues.length, header: 'Warnings', cell: ({ row }) => row.original.issues.length ? <Badge tone="warning">{row.original.issues.length}</Badge> : '—' },
  ], [])
  // TanStack Table intentionally returns stateful functions; React Compiler skips this hook.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({ data, columns, state: { sorting, globalFilter: search, columnVisibility }, onSortingChange: setSorting, onGlobalFilterChange: setSearch, onColumnVisibilityChange: (updater) => setColumnVisibility((current) => { const next = typeof updater === 'function' ? updater(current) : updater; localStorage.setItem('autords-columns', JSON.stringify(next)); return next }), getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getFilteredRowModel: getFilteredRowModel() })
  return <div className="flex h-full flex-col">
    <div className="flex items-center justify-between border-b border-slate-200 p-3"><div><p className="section-kicker">Current compiled project</p><h2 className="font-bold">Finite List of Components</h2></div><div className="flex gap-2"><Select className="w-28" aria-label="Class filter" value={classFilter} onChange={(e) => setClassFilter(e.target.value)}><option value="">All classes</option>{[...new Set(components.map((item) => item.class_code))].sort().map((code) => <option key={code}>{code}</option>)}</Select><Select className="w-28" aria-label="Status filter" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All status</option><option value="true">Valid</option><option value="false">Invalid</option></Select><label className="relative w-64"><Search className="absolute left-2 top-2 text-slate-400" size={15}/><Input className="pl-8" placeholder="Search RDS, label, class…" value={search} onChange={(event) => setSearch(event.target.value)} /></label></div></div>
    <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2 text-xs"><span className="font-semibold">{selected.size} selected</span><Select className="w-36" value={bulkClass} onChange={(e) => setBulkClass(e.target.value)}><option value="">Change class…</option>{[...new Set(components.map((item) => item.class_code))].sort().map((code) => <option key={code}>{code}</option>)}</Select><Button disabled={!selected.size || !bulkClass || bulk.isPending} onClick={() => bulk.mutate()}>Apply bulk edit</Button><div className="ml-auto flex items-center gap-2"><Columns3 size={14}/>{table.getAllLeafColumns().filter((column) => column.id !== 'designation').map((column) => <label key={column.id} className="flex items-center gap-1"><input type="checkbox" checked={column.getIsVisible()} onChange={column.getToggleVisibilityHandler()}/>{String(column.columnDef.header)}</label>)}</div></div>
    <div className="overflow-auto"><table className="w-full border-collapse text-left text-xs"><thead className="sticky top-0 z-10 bg-slate-100">{table.getHeaderGroups().map((group) => <tr key={group.id}><th className="w-8 border-b border-r border-slate-300 px-2"><input aria-label="Select all rows" type="checkbox" checked={data.length > 0 && data.every((item) => selected.has(item.id))} onChange={(e) => setSelected(e.target.checked ? new Set(data.map((item) => item.id)) : new Set())}/></th>{group.headers.map((header) => <th key={header.id} className="border-b border-r border-slate-300 px-3 py-2 font-bold uppercase tracking-wide text-slate-600"><button className="flex items-center gap-1" onClick={header.column.getToggleSortingHandler()}>{flexRender(header.column.columnDef.header, header.getContext())}{header.column.getCanSort() && <ArrowUpDown size={11}/>}</button></th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id} className={`cursor-pointer border-b border-slate-200 hover:bg-purple-50 ${selectedComponentId === row.original.id ? 'bg-purple-100' : 'odd:bg-white even:bg-slate-50'}`} onClick={() => selectComponent(row.original.id)}><td className="border-r border-slate-100 px-2" onClick={(e) => e.stopPropagation()}><input aria-label={`Select ${row.original.label}`} type="checkbox" checked={selected.has(row.original.id)} onChange={(e) => setSelected((current) => { const next = new Set(current); if (e.target.checked) next.add(row.original.id); else next.delete(row.original.id); return next })}/></td>{row.getVisibleCells().map((cell) => <td key={cell.id} className="max-w-64 border-r border-slate-100 px-3 py-2 align-top">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></div>
  </div>
}
