"""Exact dispatch preserves the existing claim/spawn path without touching sibling cards."""
from pathlib import Path
from unittest.mock import Mock
import pytest
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_db_dispatch as kbd

@pytest.fixture
def conn(tmp_path, monkeypatch, all_assignees_spawnable):
    home = tmp_path / '.hermes'
    home.mkdir()
    monkeypatch.setenv('HERMES_HOME', str(home))
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(kbd, '_memory_pressure_level', lambda: 'normal')
    kb.init_db()
    with kbc.connect() as connection:
        yield connection

def test_exact_dispatch_leaves_siblings_untouched_and_never_repeats(conn, monkeypatch):
    other = kb.create_task(conn, title='Sibling ready', assignee='worker', priority=99)
    target = kb.create_task(conn, title='Target', assignee='worker')
    triage = kb.create_task(conn, title='Unreleased sibling', assignee='worker', triage=True)
    before = {tid: dict(conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()) for tid in [other, triage]}
    maintenance = Mock(side_effect=AssertionError('targeted dispatch must not run board maintenance'))
    monkeypatch.setattr(kbd, '_run_reclaim_phase', maintenance)
    spawned = []
    result = kbd.dispatch_once(conn, task_id=target, spawn_fn=lambda t, w, **k: spawned.append(t.id))
    assert spawned == [target]
    assert [t for t, _, _ in result.spawned] == [target]
    assert kbd.dispatch_once(conn, task_id=target, spawn_fn=lambda *a, **k: pytest.fail('duplicate spawn')).spawned == []
    assert kb.get_task(conn, target).status == 'running'
    for tid, row in before.items():
        assert dict(conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()) == row
    maintenance.assert_not_called()

def test_exact_dispatch_keeps_release_dependency_and_lock_gates(conn):
    triage = kb.create_task(conn, title='Not released', assignee='worker', triage=True)
    spawn = Mock()
    assert kbd.dispatch_once(conn, task_id=triage, spawn_fn=spawn).spawned == []
    parent = kb.create_task(conn, title='Parent', assignee='worker')
    child = kb.create_task(conn, title='Child', assignee='worker', parents=[parent])
    # Even a stale/bad ready flag cannot bypass the existing atomic claim dependency gate.
    with kb.write_txn(conn):
        conn.execute("UPDATE tasks SET status='ready' WHERE id=?", (child,))
    assert kbd.dispatch_once(conn, task_id=child, spawn_fn=spawn).spawned == []
    assert kb.get_task(conn, child).status == 'todo'
    with kbc._dispatch_tick_lock(kb.kanban_db_path(board='default')) as held:
        assert held
        assert kbd.dispatch_once(conn, task_id=parent, spawn_fn=spawn).skipped_locked
    spawn.assert_not_called()

@pytest.mark.parametrize('task_id', ['', 'default', '../task', 't_'])
def test_invalid_target_never_dispatches_board(conn, task_id):
    with pytest.raises(ValueError, match='invalid dispatch task_id'):
        kbd.dispatch_once(conn, task_id=task_id, spawn_fn=lambda *a, **k: pytest.fail('invalid target spawned'))

def test_missing_target_and_dry_run_do_not_modify_database(conn):
    target = kb.create_task(conn, title='Target', assignee='worker')
    changes = conn.total_changes
    result = kbd.dispatch_once(conn, task_id=target, dry_run=True)
    assert [t for t, _, _ in result.spawned] == [target]
    assert kbd.dispatch_once(conn, task_id='t_missing', dry_run=True).spawned == []
    assert conn.total_changes == changes


@pytest.mark.parametrize('review_enabled', [False, True])
def test_exact_review_dispatch_preserves_lane_gate_and_siblings(conn, monkeypatch, review_enabled):
    ready = kb.create_task(conn, title='Higher-priority ready sibling', assignee='worker', priority=99)
    target = kb.create_task(conn, title='Review target', assignee='worker')
    sibling = kb.create_task(conn, title='Review sibling', assignee='worker', priority=99)
    implementation_runs = {}
    for tid in (target, sibling):
        claimed = kb.claim_task(conn, tid)
        implementation_runs[tid] = claimed.current_run_id
        assert kb.request_review(conn, tid, summary='Synthetic review handoff',
                                 reviewer='reviewer', expected_run_id=claimed.current_run_id)
    before = {tid: dict(conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone())
              for tid in (ready, sibling)}
    monkeypatch.setattr(kbd, 'review_dispatch_enabled', lambda: review_enabled)
    spawned = []
    result = kbd.dispatch_once(conn, task_id=target, max_spawn=1,
                              spawn_fn=lambda t, w, **k: spawned.append((t.id, t.assignee, t.skills)))
    if review_enabled:
        assert [t for t, _, _ in result.spawned] == [target]
        assert len(spawned) == 1
        assert spawned[0][:2] == (target, 'reviewer')
        assert 'sdlc-review' in spawned[0][2]
        task = kb.get_task(conn, target)
        assert task.status == 'running'
        assert task.current_run_id != implementation_runs[target]
        assert kbd.dispatch_once(conn, task_id=target, max_spawn=1,
                                 spawn_fn=lambda *a, **k: pytest.fail('duplicate review')).spawned == []
    else:
        assert result.spawned == [] and spawned == []
        assert kb.get_task(conn, target).status == 'review'
        assert kb.get_task(conn, target).current_run_id is None
    for tid, row in before.items():
        assert dict(conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()) == row


def test_exact_dispatch_fails_closed_when_board_lock_path_cannot_resolve(conn, monkeypatch):
    target = kb.create_task(conn, title='Must remain ready', assignee='worker')
    before = conn.total_changes
    spawn = Mock()
    hook = Mock()
    monkeypatch.setattr(kb, 'kanban_db_path', Mock(side_effect=OSError('synthetic path failure')))
    monkeypatch.setattr(kb, '_fire_dispatch_tick_hook', hook)
    with pytest.raises(OSError, match='synthetic path failure'):
        kbd.dispatch_once(conn, task_id=target, spawn_fn=spawn)
    spawn.assert_not_called()
    hook.assert_not_called()
    assert conn.total_changes == before
    assert kb.get_task(conn, target).status == 'ready'


def test_exact_dispatch_max_one_preserves_existing_running_task(conn):
    running = kb.create_task(conn, title='Existing worker', assignee='worker')
    assert kb.claim_task(conn, running) is not None
    target = kb.create_task(conn, title='Wait for capacity', assignee='worker')
    before = conn.total_changes
    rows = {tid: dict(conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone())
            for tid in (running, target)}
    spawn = Mock()
    result = kbd.dispatch_once(conn, task_id=target, max_spawn=1, spawn_fn=spawn)
    assert result.spawned == []
    spawn.assert_not_called()
    assert conn.total_changes == before
    for tid, row in rows.items():
        assert dict(conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()) == row
