# Hermes-Agent — Context Compression "Maximal" Plan

Status: PLAN (niet gebouwd). Gebaseerd op code-map + SOTA-research (juni 2026).
Live module: `agent/context_compressor.py` (1749 r.), trigger `conversation_loop.py:3657`,
construct `agent/agent_init.py:1446`, per-model threshold `agent/auxiliary_client.py:227`.

## Research-conclusie (wat is "best")
Convergente best-practice (Anthropic compaction, Manus, Claude Code, ACON/Focus 2026):
- Bescherm **head** (system+1e taak) en **tail** (recente turns); prune herhaalbare tool-results
  eerst goedkoop; vat **midden** samen met **gestructureerd template**.
- **Cumulatief**: elke compaction bouwt voort op vorige summary, niet overschrijven.
- **Behoud reasoning** (waarom approach B verworpen), niet alleen uitkomst.
- **Reversibel** (Manus): bij droppen tool-output pointer (pad/URL) bewaren voor re-fetch.
- **Token-telling**: echte tokenizer voor *budget/kosten*; char/4 is OK puur voor *trigger*
  (10% marge acceptabel). Hermes gebruikt al echte API-counts (`last_prompt_tokens`) → laag prio.
- **Trigger-moment**: ~60% is "scherp"; later (0.82) = meer context-rot, minder aux-cost. Tradeoff.
- Must-follow regels horen in persistente memory (CLAUDE.md/SOUL.md), niet in lossy summary.

## A. Echte bugs (robustheid eerst) — bevestigd door gepubliceerde Hermes-analyse
1. **Anti-thrash lock zonder decay** — `should_compress()` geeft permanent False na 2
   ineffectieve compressies (`context_compressor.py:~625`, gate `_ineffective_compression_count>=2`).
   Fix: time/turn-based decay (reset na N turns of M tokens groei). Maak drempel configureerbaar.
2. **Tool-ordering 400** — als 1e tail-message role=`tool` is, breekt ingevoegde summary de
   API-eis (tool moet na assistant met tool_calls) → HTTP 400 op OpenAI-compatible providers.
   Fix: boundary forward-align over tool-paren (Phase 2/4 in `compress()` ~1552-1561, `_sanitize_tool_pairs`).
3. **Silent summary drop** — malformed aux-JSON faalt stil → midden gedropt zonder samenvatting.
   Fix: harde validatie + retry (bestaat deels), bij eindfaal duidelijke fallback-summary met
   "N turns niet samengevat door aux-fout" i.p.v. stille drop.

## B. Kwaliteit (summary-template) — uit production-tested compaction-memory
Uitbreiden van `_generate_summary()` prompt-template met verplichte secties:
- **Historical Context** (cumulatief, bovenaan): `[Compaction k]: actie + reden (3-5 zinnen)`.
- **Decisions**: `Decision: X. Why: Y. Rejected: Z.`
- **Findings**: `[P0] bug: desc (1-line fix)` / `[P1] risk: desc`.
- **Blockers & Dependencies**: `[A] blocks [B]`, `[C] waiting on [D]`.
- **Verbatim user-correcties** (quote, niet paraphraseren) → voorkomt terugval.
Behoud bestaande Goal/Progress/Files/Next-Steps. Iteratieve update bestaat al → benutten.

## C. Reversibiliteit (Manus) — laag risico, hoge winst
Phase-1 tool-pruning (`_prune_old_tool_results` ~640): bij vervangen door 1-regel summary ook
**re-fetch pointer** bewaren (bestandspad/URL/command) zodat agent later kan herhalen i.p.v.
permanent verlies. (Past op `terminal`/`read_file` results.)

## D. Hardcoded → config (door jou gekozen)
Nieuwe knoppen via config.yaml `compression:` + env, met huidige waarden als default:
| Knop | Nu (hardcoded) | Locatie |
|------|----------------|---------|
| anti-thrash gate count | 2 | context_compressor.py ~625 |
| anti-thrash savings %% | 10%% | idem |
| anti-thrash decay (turns) | (geen) | NIEUW |
| summary token ceiling | 12_000 | context_compressor.py:54-75 |
| chars-per-token | 4 | context_compressor.py:79 |
| image token estimate | 1600 | idem |
| keep-pointer on prune | (geen) | NIEUW |

## E. Threshold-tuning (config-only, geen engine-wijziging)
- Default `compression.threshold` 0.50; per-model override-tabel in `auxiliary_client.py:227`.
- Voor `deepseek-v4-pro:cloud` (1M ctx): 0.82 = laat → overweeg 0.65-0.70 voor scherpte,
  óf hou 0.82 als kosten/aux-calls prioriteit zijn. Beslissing van Kenny.

## Risico & volgorde
1. (laag) D config-knoppen + E threshold — additive, geen gedragsverandering bij defaults.
2. (laag) C reversibele pointers — alleen extra info in prune-summary.
3. (midden) A1 anti-thrash decay — verandert trigger-gedrag; test met eval-set.
4. (midden) A2 tool-ordering — raakt assembly; unit-test met tool-role-first tail.
5. (midden) B template — kwaliteit; valideer op ≥50 representatieve sessies (research-advies).
6. (laag/optioneel) token-tokenizer — Hermes gebruikt al API-counts; alleen pre-flight nauwkeuriger.

## Verificatie per stap
- `python -m py_compile` + bestaande tests (`tests/`, 1019 tests groen volgens history).
- Gerichte unit-test voor A2 (tool-role-first tail → geen 400).
- Eval op echte sessie-transcripts voor B (geen accuracy-regressie).
