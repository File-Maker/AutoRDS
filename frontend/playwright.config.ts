import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig } from '@playwright/test'

const windowsPython = resolve('../backend/.venv/Scripts/python.exe')
const python = existsSync(windowsPython) ? windowsPython : 'python'
const dataDirectory = process.env.AUTORDS_DATA_DIR ?? resolve('../.tmp/e2e')

export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  expect: { timeout: 10_000 },
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
  webServer: [
    { command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8134`, cwd: '../backend', env: { AUTORDS_DATA_DIR: dataDirectory }, url: 'http://127.0.0.1:8134/api/health', reuseExistingServer: true, timeout: 60_000 },
    { command: 'pnpm dev', cwd: '.', url: 'http://127.0.0.1:5173', reuseExistingServer: true, timeout: 60_000 },
  ],
})
