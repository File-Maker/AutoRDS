import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ManualBuilder } from '../components/ManualBuilder'

vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ designation: '=M2-M1', valid: true, issues: [] }) })))

describe('ManualBuilder', () => {
  it('explains that designations come from the compiler', () => {
    const project = { id: 'p', name: 'Test', description: '', ruleset_id: 'ee3_2026_27', functions: [{ id: 'f', project_id: 'p', number: 2, label: 'Joint 2', description: '', parent_id: null }], components: [], relations: [], validation: [] }
    const ruleset = { id: 'ee3_2026_27', name: 'EE3', version: '1.0.0', classes: { M: { name: 'driving_object', aliases: ['motor'] } } }
    render(<QueryClientProvider client={new QueryClient()}><ManualBuilder project={project} ruleset={ruleset}/></QueryClientProvider>)
    expect(screen.getByText(/Preview and final designation are compiled by the backend/)).toBeInTheDocument()
  })
})
