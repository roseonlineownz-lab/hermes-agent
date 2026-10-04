import path from 'node:path'
import { stat } from 'node:fs/promises'

/** Probe remembered workspaces without blocking Electron on offline UNC/WSL paths.
 * A deadline is not evidence that a path was deleted, so callers must preserve
 * the saved workspace when this rejects instead of selecting a new directory.
 */
async function workspaceDirectoryExists(
  dir: string,
  { timeoutMs = 3000, probe = stat }: {
    timeoutMs?: number
    probe?: (dir: string) => Promise<{ isDirectory(): boolean }>
  } = {}
): Promise<boolean> {
  let timer: ReturnType<typeof setTimeout>
  const deadline = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => reject(new Error('Workspace directory check timed out; the saved workspace has been preserved.')), timeoutMs)
  })
  try {
    return (await Promise.race([probe(dir), deadline])).isDirectory()
  } catch (error) {
    if (error?.code === 'ENOENT' || error?.code === 'ENOTDIR') return false
    throw error
  } finally {
    clearTimeout(timer)
  }
}

/** True when `dir` lives inside a packaged app bundle / install tree. */
function isPackagedInstallPath(dir, { installRoots, isPackaged }: { installRoots: string[]; isPackaged: boolean }) {
  if (!isPackaged || !dir) {
    return false
  }

  let resolved

  try {
    resolved = path.resolve(String(dir))
  } catch {
    return false
  }

  const roots = new Set((installRoots ?? []).filter(Boolean).map(candidate => path.resolve(String(candidate))))

  for (const root of roots) {
    if (resolved === root) {
      return true
    }

    const rel = path.relative(root, resolved) as any

    if (rel && !rel.startsWith('..') && !path.isAbsolute(rel)) {
      return true
    }
  }

  return false
}

export { isPackagedInstallPath, workspaceDirectoryExists }
