import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { I18nProvider } from '@/i18n'
import { $activeSessionId, $awaitingResponse, $busy, $currentCwd, $gatewayState, $turnStartedAt } from '@/store/session'
import { $subagentsBySession, upsertSubagent } from '@/store/subagents'

import { AgentsView } from './index'

function renderAgentsView() {
  return render(
    <I18nProvider configClient={null}>
      <AgentsView onClose={() => undefined} />
    </I18nProvider>
  )
}

describe('AgentsView spawn tree', () => {
  beforeEach(() => {
    Object.defineProperty(HTMLElement.prototype, 'animate', {
      configurable: true,
      value: vi.fn()
    })

    $activeSessionId.set('session-1234567890')
    $awaitingResponse.set(false)
    $busy.set(false)
    $currentCwd.set('/home/faramix')
    $gatewayState.set('open')
    $subagentsBySession.set({})
    $turnStartedAt.set(null)
  })

  afterEach(() => {
    cleanup()
    $activeSessionId.set(null)
    $awaitingResponse.set(false)
    $busy.set(false)
    $currentCwd.set('')
    $gatewayState.set('idle')
    $subagentsBySession.set({})
    $turnStartedAt.set(null)
  })

  it('explains why the spawn tree is empty', () => {
    renderAgentsView()

    expect(screen.getByText('No live subagents')).toBeTruthy()
    expect(screen.getByText('Live diagnosis')).toBeTruthy()
    expect(screen.getByText('delegate_task / subagent.* events')).toBeTruthy()
    expect(screen.getByText(/Nova\/EventBus background agents stay outside this stream/)).toBeTruthy()
    expect(screen.getByText('/home/faramix')).toBeTruthy()
  })

  it('renders real delegated subagents without the empty diagnosis', () => {
    upsertSubagent('session-1234567890', {
      goal: 'scan workspace',
      status: 'running',
      subagent_id: 'worker-1',
      task_index: 0
    })

    renderAgentsView()

    expect(screen.getByText('scan workspace')).toBeTruthy()
    expect(screen.queryByText('Live diagnosis')).toBeNull()
  })
})
