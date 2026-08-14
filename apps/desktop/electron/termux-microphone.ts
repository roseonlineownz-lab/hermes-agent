import { spawn } from 'node:child_process'
import { randomUUID } from 'node:crypto'

const DEFAULT_TERMUX_HOST = 's25'
const HOST_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9._-]*$/
const MAX_RECORDING_BYTES = 32 * 1024 * 1024
const STATUS_CACHE_MS = 30_000

interface CommandResult {
  stderr: string
  stdout: Buffer
}

export type RemoteCommandRunner = (args: string[], timeoutMs?: number) => Promise<CommandResult>

export interface TermuxMicrophoneStatus {
  available: boolean
  host: string
}

export interface TermuxMicrophoneRecording {
  data: Uint8Array
  mimeType: 'audio/aac'
}

interface TermuxMicrophoneBridgeOptions {
  host?: string
  runner?: RemoteCommandRunner
}

function termuxApiError(result: CommandResult): null | string {
  const output = `${result.stdout.toString('utf8')}\n${result.stderr}`.trim()

  if (!output) {return null}

  try {
    const payload = JSON.parse(output) as { error?: unknown }

    return typeof payload.error === 'string' && payload.error.trim() ? payload.error.trim() : null
  } catch {
    return /"error"\s*:/i.test(output) ? output : null
  }
}

function runProcess(command: string, args: string[], timeoutMs: number): Promise<CommandResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true })
    const stdout: Buffer[] = []
    const stderr: Buffer[] = []
    let outputBytes = 0
    let settled = false

    const finish = (error?: Error, result?: CommandResult) => {
      if (settled) {return}
      settled = true
      clearTimeout(timer)

      if (error) {reject(error)}
      else {resolve(result!)}
    }

    const timer = setTimeout(() => {
      child.kill()
      finish(new Error(`Termux microphone command timed out after ${timeoutMs}ms`))
    }, timeoutMs)

    child.stdout.on('data', (chunk: Buffer) => {
      outputBytes += chunk.length

      if (outputBytes > MAX_RECORDING_BYTES) {
        child.kill()
        finish(new Error('Termux microphone recording exceeded 32 MiB'))

        return
      }

      stdout.push(chunk)
    })
    child.stderr.on('data', (chunk: Buffer) => stderr.push(chunk))
    child.on('error', error => finish(error))
    child.on('close', code => {
      const result = {
        stderr: Buffer.concat(stderr).toString('utf8').trim(),
        stdout: Buffer.concat(stdout)
      }

      if (code === 0) {finish(undefined, result)}
      else {finish(new Error(result.stderr || `Termux microphone command exited with code ${code}`))}
    })
  })
}

function createSshRunner(host: string): RemoteCommandRunner {
  return (remoteArgs, timeoutMs = 15_000) => {
    const sshArgs = [
      '-o',
      'BatchMode=yes',
      '-o',
      'ConnectTimeout=5',
      host,
      ...remoteArgs
    ]

    return process.platform === 'win32'
      ? runProcess('wsl.exe', ['-e', 'ssh', ...sshArgs], timeoutMs)
      : runProcess('ssh', sshArgs, timeoutMs)
  }
}

export class TermuxMicrophoneBridge {
  private readonly host: string
  private readonly runner: RemoteCommandRunner
  private recordingPath: null | string = null
  private statusCache: null | { checkedAt: number; status: TermuxMicrophoneStatus } = null

  constructor(options: TermuxMicrophoneBridgeOptions = {}) {
    this.host = (options.host ?? process.env.HERMES_TERMUX_MIC_SSH_HOST ?? DEFAULT_TERMUX_HOST).trim()
    this.runner = options.runner ?? createSshRunner(this.host)
  }

  async status(): Promise<TermuxMicrophoneStatus> {
    if (!HOST_PATTERN.test(this.host)) {
      return { available: false, host: this.host }
    }

    if (this.statusCache && Date.now() - this.statusCache.checkedAt < STATUS_CACHE_MS) {
      return this.statusCache.status
    }

    let available = false

    try {
      const result = await this.runner(['termux-microphone-record', '-i'], 8_000)
      available = termuxApiError(result) === null
    } catch {
      available = false
    }

    const status = { available, host: this.host }
    this.statusCache = { checkedAt: Date.now(), status }

    return status
  }

  async start(): Promise<void> {
    if (this.recordingPath) {return}
    const status = await this.status()

    if (!status.available) {
      throw new Error(`Termux microphone is unavailable on SSH host ${this.host}`)
    }

    const path = `/data/data/com.termux/files/usr/tmp/hermes-desktop-${randomUUID().replaceAll('-', '')}.aac`

    const result = await this.runner([
      'termux-microphone-record',
      '-f',
      path,
      '-l',
      '120',
      '-e',
      'aac',
      '-r',
      '16000',
      '-c',
      '1'
    ])

    const apiError = termuxApiError(result)

    if (apiError) {
      this.statusCache = { checkedAt: Date.now(), status: { available: false, host: this.host } }
      throw new Error(`Termux microphone refused capture: ${apiError}`)
    }

    this.recordingPath = path
  }

  async stop(): Promise<null | TermuxMicrophoneRecording> {
    const path = this.recordingPath

    if (!path) {return null}
    this.recordingPath = null

    try {
      const stopResult = await this.runner(['termux-microphone-record', '-q'])
      const apiError = termuxApiError(stopResult)

      if (apiError) {throw new Error(`Termux microphone refused stop: ${apiError}`)}

      const result = await this.runner(['cat', path], 30_000)

      if (!result.stdout.length) {return null}

      return { data: new Uint8Array(result.stdout), mimeType: 'audio/aac' }
    } finally {
      await this.runner(['rm', '-f', path]).catch(() => undefined)
    }
  }

  async cancel(): Promise<void> {
    const path = this.recordingPath

    if (!path) {return}
    this.recordingPath = null
    await this.runner(['termux-microphone-record', '-q']).catch(() => undefined)
    await this.runner(['rm', '-f', path]).catch(() => undefined)
  }
}
