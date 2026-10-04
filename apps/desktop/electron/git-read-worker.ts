import { parentPort, workerData } from 'node:worker_threads'

import {
  fileDiffVsHead, repoStatus, reviewCommitContext, reviewDiff, reviewList,
  reviewPrList, reviewRevParse, reviewShipInfo
} from './git-review-ops'
import { setNoConsoleGitRoots } from './no-console-git'
import type { GitReadRequest } from './git-read-worker-client'

const operations = { fileDiffVsHead, repoStatus, reviewCommitContext, reviewDiff, reviewList, reviewPrList, reviewRevParse, reviewShipInfo }

async function main() {
  const { operation, args, roots } = workerData as GitReadRequest
  if (!Object.hasOwn(operations, operation)) throw new Error('Unsupported Git read operation.')
  setNoConsoleGitRoots(roots)
  const fn = operations[operation as keyof typeof operations] as (...values: unknown[]) => Promise<unknown>
  return fn(...args)
}

void main().then(
  value => parentPort?.postMessage({ ok: true, value }),
  error => parentPort?.postMessage({ ok: false, error: error instanceof Error ? error.message : 'Git workspace check failed.' })
)
