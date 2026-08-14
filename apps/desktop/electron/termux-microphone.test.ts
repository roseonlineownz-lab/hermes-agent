import { describe, expect, it, vi } from 'vitest'

import { type RemoteCommandRunner, TermuxMicrophoneBridge } from './termux-microphone'

describe('TermuxMicrophoneBridge', () => {
  it('records on Termux and returns the captured AAC without using Chromium audio', async () => {
    const calls: string[][] = []

    const runner: RemoteCommandRunner = vi.fn(async args => {
      calls.push(args)

      if (args[0] === 'cat') {
        return { stderr: '', stdout: Buffer.from('aac-audio') }
      }

      if (args[1] === '-i') {
        return { stderr: '', stdout: Buffer.from('{"isRecording":false}') }
      }

      return { stderr: '', stdout: Buffer.alloc(0) }
    })

    const bridge = new TermuxMicrophoneBridge({ host: 's25', runner })

    await expect(bridge.status()).resolves.toEqual({ available: true, host: 's25' })
    await bridge.start()
    const recording = await bridge.stop()

    expect(recording?.mimeType).toBe('audio/aac')
    expect(recording?.data).toEqual(new Uint8Array(Buffer.from('aac-audio')))
    expect(calls.some(args => args.includes('termux-microphone-record') && args.includes('-l'))).toBe(true)
    expect(calls.some(args => args[0] === 'termux-microphone-record' && args[1] === '-q')).toBe(true)
    expect(calls.some(args => args[0] === 'rm' && args[1] === '-f')).toBe(true)
  })

  it('rejects unsafe SSH host values before spawning anything', async () => {
    const runner: RemoteCommandRunner = vi.fn()
    const bridge = new TermuxMicrophoneBridge({ host: 's25; reboot', runner })

    await expect(bridge.status()).resolves.toEqual({ available: false, host: 's25; reboot' })
    expect(runner).not.toHaveBeenCalled()
  })

  it('rejects a host value that could be interpreted as an SSH option', async () => {
    const runner: RemoteCommandRunner = vi.fn()
    const bridge = new TermuxMicrophoneBridge({ host: '-oProxyCommand=bad', runner })

    await expect(bridge.status()).resolves.toEqual({ available: false, host: '-oProxyCommand=bad' })
    expect(runner).not.toHaveBeenCalled()
  })

  it('reports unavailable when Android has not granted RECORD_AUDIO', async () => {
    const runner: RemoteCommandRunner = vi.fn(async () => ({
      stderr: '',
      stdout: Buffer.from('{"error":"Please grant android.permission.RECORD_AUDIO"}')
    }))

    const bridge = new TermuxMicrophoneBridge({ host: 's25', runner })

    await expect(bridge.status()).resolves.toEqual({ available: false, host: 's25' })
    await expect(bridge.start()).rejects.toThrow('unavailable')
  })
})
