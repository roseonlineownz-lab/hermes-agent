import { Worker } from 'node:worker_threads'
import { fileURLToPath, pathToFileURL } from 'node:url'

export interface GitReadRequest {
  operation: string
  args: unknown[]
  roots: string[]
}

// Even an asynchronous child-process API enters native spawn synchronously.
// An unavailable UNC/WSL cwd must never make Electron's main thread wait there.
export function createGitReadRunner({
  // Desktop packaging unpacks dist. Node workers load the real file directly
  // instead of depending on Electron's virtual ASAR filesystem in a new isolate.
  workerUrl = pathToFileURL(fileURLToPath(new URL('./git-read-worker.cjs', import.meta.url))
    .replace(/([\\/])app\.asar([\\/])/, '$1app.asar.unpacked$2')),
  timeoutMs = 30_000,
  maxWorkers = 4
}: { workerUrl?: URL; timeoutMs?: number; maxWorkers?: number } = {}) {
  const pending = new Map<string, Promise<unknown>>()
  let active = 0

  return function runGitRead(request: GitReadRequest): Promise<unknown> {
    const key = JSON.stringify(request)
    const existing = pending.get(key)
    if (existing) return existing
    if (active >= maxWorkers) return Promise.reject(new Error('Git is still checking another workspace. Try again shortly.'))

    active += 1
    const result = new Promise((resolve, reject) => {
      let worker: Worker
      try {
        worker = new Worker(workerUrl, { workerData: request })
      } catch (error) {
        active -= 1
        reject(error)
        return
      }
      let settled = false
      const finish = (error?: Error, value?: unknown) => {
        if (settled) return
        settled = true
        clearTimeout(timer)
        error ? reject(error) : resolve(value)
        // Do not await termination: a native filesystem call may still be blocked.
        void worker.terminate().catch(() => {})
      }
      const timer = setTimeout(() => finish(new Error('Git workspace check timed out. The workspace may be unavailable.')), timeoutMs)
      worker.once('message', message => {
        if (message?.ok === true) finish(undefined, message.value)
        else finish(new Error(message?.error || 'Git workspace check failed.'))
      })
      worker.once('error', error => finish(error))
      worker.once('exit', code => {
        active -= 1
        if (!settled) finish(new Error(`Git workspace worker exited before responding (${code}).`))
      })
      worker.unref()
    })
    pending.set(key, result)
    void result.then(() => pending.delete(key), () => pending.delete(key))
    return result
  }
}

export const runGitRead = createGitReadRunner()
