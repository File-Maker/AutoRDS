import { expect, test } from '@playwright/test'

test('complete deterministic milestone and portable round trip', async ({ page, request }) => {
  const projectName = `E2E ${Date.now()}`
  const created = await request.post('http://127.0.0.1:8134/api/projects', { data: { name: projectName } })
  expect(created.ok()).toBeTruthy()
  const project = await created.json()
  const withFunction = await (await request.post(`http://127.0.0.1:8134/api/projects/${project.id}/functions`, { data: { number: 2, label: 'Joint 2' } })).json()
  const functionId = withFunction.functions[0].id
  const motor = await (await request.post(`http://127.0.0.1:8134/api/projects/${project.id}/components`, { data: { function_id: functionId, class_code: 'M', label: 'Motor' } })).json()
  expect(motor.designation).toBe('=M2-M1')
  const encoder = await (await request.post(`http://127.0.0.1:8134/api/projects/${project.id}/components`, { data: { function_id: functionId, parent_component_id: motor.id, class_code: 'B', label: 'Encoder' } })).json()
  expect(encoder.designation).toBe('=M2-M1.B1')
  const moved = await (await request.patch(`http://127.0.0.1:8134/api/components/${encoder.id}`, { data: { parent_component_id: null } })).json()
  expect(moved.designation).toBe('=M2-B1')
  const undone = await (await request.post(`http://127.0.0.1:8134/api/projects/${project.id}/undo`)).json()
  expect(undone.components.find((item: { id: string }) => item.id === encoder.id).designation).toBe('=M2-M1.B1')

  await page.goto('/')
  await page.getByLabel('Current project').selectOption(project.id)
  await page.getByRole('button', { name: /FLoC/ }).click()
  await expect(page.getByText('=M2-M1.B1')).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: /FLoC/ }).click()
  await expect(page.getByText('=M2-M1.B1')).toBeVisible()

  const portable = await request.get(`http://127.0.0.1:8134/api/projects/${project.id}/portable`)
  expect(portable.ok()).toBeTruthy()
  const importedResponse = await request.post('http://127.0.0.1:8134/api/projects/import', { multipart: { file: { name: `${projectName}.autords`, mimeType: 'application/zip', buffer: await portable.body() } } })
  expect(importedResponse.ok()).toBeTruthy()
  const imported = await importedResponse.json()
  expect(imported.components.map((item: { designation: string }) => item.designation)).toEqual(['=M2-M1', '=M2-M1.B1'])
  const xlsx = await request.get(`http://127.0.0.1:8134/api/projects/${imported.id}/export/xlsx`)
  expect(xlsx.ok()).toBeTruthy()
  expect((await xlsx.body()).length).toBeGreaterThan(1000)
  const validation = await (await request.post(`http://127.0.0.1:8134/api/projects/${imported.id}/validate`)).json()
  expect(validation.issues.filter((item: { severity: string }) => item.severity === 'ERROR')).toEqual([])
})
