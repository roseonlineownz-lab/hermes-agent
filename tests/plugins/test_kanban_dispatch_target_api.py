"""The existing authenticated Kanban API forwards exact task selection, never widens it."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_dispatch as kbd

@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / '.hermes'
    home.mkdir()
    monkeypatch.setenv('HERMES_HOME', str(home))
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    kb.init_db()
    spec = importlib.util.spec_from_file_location('kanban_target_api_test', Path(__file__).resolve().parents[2] / 'plugins/kanban/dashboard/plugin_api.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router, prefix='/api/plugins/kanban')
    return TestClient(app)

def test_dispatch_forwards_exact_target_and_rejects_invalid(client, monkeypatch):
    dispatch = Mock(return_value=kbd.DispatchResult())
    monkeypatch.setattr(kbd, 'dispatch_once', dispatch)
    response = client.post('/api/plugins/kanban/dispatch?board=default&task_id=t_proof&max=1')
    assert response.status_code == 200
    assert dispatch.call_args.kwargs == {'dry_run': False, 'max_spawn': 1, 'board': 'default', 'task_id': 't_proof'}
    dispatch.reset_mock()
    assert client.post('/api/plugins/kanban/dispatch?board=default&task_id=').status_code == 422
    dispatch.assert_not_called()

def test_legacy_board_dispatch_remains_unfiltered(client, monkeypatch):
    dispatch = Mock(return_value=kbd.DispatchResult())
    monkeypatch.setattr(kbd, 'dispatch_once', dispatch)
    assert client.post('/api/plugins/kanban/dispatch?board=default').status_code == 200
    assert dispatch.call_args.kwargs['task_id'] is None
