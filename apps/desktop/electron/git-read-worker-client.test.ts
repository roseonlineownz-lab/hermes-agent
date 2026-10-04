import assert from 'node:assert/strict'
import { test } from 'vitest'
import { createGitReadRunner } from './git-read-worker-client'

const workerUrl = new URL(`data:text/javascript,${encodeURIComponent(`
  import { parentPort, workerData } from 'node:worker_threads';
  if (workerData.operation === 'crash') throw new Error('worker failure');
  if (workerData.operation === 'exit') process.exit(0);
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, workerData.args[0]);
  parentPort.postMessage({ ok: true, value: workerData.args[1] });
`)}`)

test('blocked worker leaves the main event loop responsive and preserves the result', async () => {
  const run = createGitReadRunner({ workerUrl, timeoutMs: 3000 })
  let ticks = 0
  const timer = setInterval(() => ticks++, 10)
  try {
    assert.deepEqual(await run({ operation: 'read', args: [180, { files: ['actual'] }], roots: [] }), { files: ['actual'] })
    assert.ok(ticks >= 5, `main loop only ticked ${ticks} times`)
  } finally { clearInterval(timer) }
})

test('identical pending reads share a worker and concurrent work is bounded', async () => {
  const run = createGitReadRunner({ workerUrl, maxWorkers: 1, timeoutMs: 3000 })
  const request = { operation: 'read', args: [100, 'done'], roots: [] }
  const first = run(request)
  assert.equal(run(request), first)
  await assert.rejects(run({ ...request, args: [100, 'other'] }), /still checking/)
  assert.equal(await first, 'done')
})

test('blocked reads time out instead of waiting indefinitely', async () => {
  const run = createGitReadRunner({ workerUrl, timeoutMs: 100 })
  await assert.rejects(run({ operation: 'read', args: [5000, 'late'], roots: [] }), /timed out/)
})

test('worker errors and premature exits reject the caller', async () => {
  const run = createGitReadRunner({ workerUrl, timeoutMs: 3000 })
  await assert.rejects(run({ operation: 'crash', args: [], roots: [] }), /worker failure/)
  await assert.rejects(run({ operation: 'exit', args: [], roots: [] }), /exited before responding/)
})
