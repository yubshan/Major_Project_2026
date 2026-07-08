# Suwarna's Decision Logic Roadmap

This folder is a self-contained roadmap for Suwarna's portion of Project Drisya: the `modules/decision_logic` system.

It is intentionally kept inside `modules/decision_logic/suwarna_roadmap/` so it does not interfere with teammates' work, shared contracts, simulator files, navigation files, or WiFi detection files.

## What This Folder Contains

| File | Purpose |
|---|---|
| `roadmap.md` | Main detailed roadmap for building the Decision Logic module. |
| `mini_projects.md` | Checkbox-based mini-projects that can become GitHub milestones and LinkedIn posts. |
| `blackboard_contract_draft.md` | A draft contract to discuss with teammates before implementation. |
| `github_linkedin_packaging.md` | How to present the work honestly and professionally. |

## How To Use This Roadmap

Start with `roadmap.md`. Then complete each mini-project from `mini_projects.md` in order.

The important rule: build a reliable safety-first decision system before touching reinforcement learning.

Recommended order:

1. Freeze Blackboard contracts with the team.
2. Build typed input validation.
3. Build a safety-first Behavior Tree.
4. Add victim detection response.
5. Add deterministic exploration.
6. Add explainability traces.
7. Add RL only after the baseline works.

## Current Project Reality

The current `modules/decision_logic` folder only contains a README. Most shared files are also still contract placeholders. So this roadmap focuses first on contracts, testability, safety, and integration discipline.

Do not claim real hardware performance, rescue success rate, or complete autonomy until those are actually measured.

