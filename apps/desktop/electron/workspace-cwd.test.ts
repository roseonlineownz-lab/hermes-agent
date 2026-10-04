/**
 * Tests for electron/workspace-cwd.ts.
 *
 * Run with: node --test electron/workspace-cwd.test.ts
 */

import assert from 'node:assert/strict'
import path from 'node:path'
import fs from 'node:fs/promises'
import os from 'node:os'

import { test } from 'vitest'

import { isPackagedInstallPath, workspaceDirectoryExists } from './workspace-cwd'

const installRoot = path.resolve('/opt/Hermes')

test('workspace probe distinguishes existing directories, files, and missing paths', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'hermes-workspace-probe-'))
  try {
    await fs.writeFile(path.join(dir, 'file'), 'test')
    assert.equal(await workspaceDirectoryExists(dir), true)
    assert.equal(await workspaceDirectoryExists(path.join(dir, 'file')), false)
    assert.equal(await workspaceDirectoryExists(path.join(dir, 'missing')), false)
  } finally { await fs.rm(dir, { recursive: true, force: true }) }
})

test('unavailable workspace times out while the main loop remains responsive', async () => {
  let ticks = 0
  const timer = setInterval(() => ticks++, 5)
  try {
    await assert.rejects(workspaceDirectoryExists('unavailable', {
      timeoutMs: 60,
      probe: () => new Promise(() => {})
    }), /saved workspace has been preserved/)
    assert.ok(ticks >= 3)
  } finally { clearInterval(timer) }
})

test('access failures are not misclassified as deleted workspaces', async () => {
  await assert.rejects(workspaceDirectoryExists('denied', {
    probe: () => Promise.reject(Object.assign(new Error('Access denied'), { code: 'EACCES' }))
  }), /Access denied/)
})

test('isPackagedInstallPath returns false when not packaged', () => {
  assert.equal(isPackagedInstallPath(installRoot, { isPackaged: false, installRoots: [installRoot] }), false)
})

test('isPackagedInstallPath flags the install root itself', () => {
  assert.equal(isPackagedInstallPath(installRoot, { isPackaged: true, installRoots: [installRoot] }), true)
})

test('isPackagedInstallPath flags paths nested under the install root', () => {
  const nested = path.join(installRoot, 'resources', 'app.asar')

  assert.equal(isPackagedInstallPath(nested, { isPackaged: true, installRoots: [installRoot] }), true)
})

test('isPackagedInstallPath ignores paths outside the install root', () => {
  const homeProject = path.resolve('/home/user/projects/demo')

  assert.equal(isPackagedInstallPath(homeProject, { isPackaged: true, installRoots: [installRoot] }), false)
})
