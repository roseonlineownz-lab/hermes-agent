from hermes_cli.cron import cron_list


def test_cron_list_handles_null_repeat(monkeypatch, capsys):
    from cron import jobs as cron_jobs

    monkeypatch.setattr(
        cron_jobs,
        "list_jobs",
        lambda include_disabled=False: [
            {
                "id": "healthcheck30m",
                "name": "Ecosystem Health Check",
                "schedule_display": "every 30m",
                "state": "scheduled",
                "next_run_at": "2026-05-18T05:30:00+02:00",
                "repeat": None,
                "deliver": ["local"],
            }
        ],
    )

    cron_list()

    out = capsys.readouterr().out
    assert "healthcheck30m" in out
    assert "Repeat:" in out
