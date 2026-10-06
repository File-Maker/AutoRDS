import { create } from 'zustand'

type WorkspaceState = {
  projectId: string | null
  selectedComponentId: string | null
  activeView: 'builder' | 'floc' | 'graph' | 'inference' | 'validation' | 'history'
  search: string
  setProject: (id: string | null) => void
  selectComponent: (id: string | null) => void
  setView: (view: WorkspaceState['activeView']) => void
  setSearch: (search: string) => void
}

export const useWorkspace = create<WorkspaceState>((set) => ({
  projectId: localStorage.getItem('autords-project'), selectedComponentId: null,
  activeView: 'builder', search: '',
  setProject: (projectId) => { if (projectId) localStorage.setItem('autords-project', projectId); else localStorage.removeItem('autords-project'); set({ projectId, selectedComponentId: null }) },
  selectComponent: (selectedComponentId) => set({ selectedComponentId }),
  setView: (activeView) => set({ activeView }), setSearch: (search) => set({ search }),
}))
