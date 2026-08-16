# GitHub And LinkedIn Packaging Guide

This guide helps present Suwarna's Decision Logic work honestly and strongly.

## GitHub Project Standard

Every mini-project should include:

- Clear README section.
- Clean folder structure.
- Unit tests.
- Example input and output.
- Scenario result if applicable.
- Limitations.
- Next step.

## Strong Module README Structure

Use this structure later in `modules/decision_logic/README.md` after implementation starts:

```text
# Decision Logic Module

## Purpose
High-level robot decision system for Project Drisya.

## Architecture
Blackboard -> State Snapshot -> Behavior Tree -> Commands + Trace.

## Blackboard Contract
Inputs and outputs with schemas.

## Behavior Tree
Priority order and node descriptions.

## Running Locally
Dry-run and test commands.

## Scenario Tests
Scenario table with pass/fail status.

## Results
Only measured results.

## Limitations
Current gaps.

## Next Steps
Integration, RL, hardware validation.
```

## Good LinkedIn Post Template

```text
I built [specific component] for Project Drisya, an autonomous search-and-rescue robot.

Problem:
[The exact technical issue.]

Approach:
[Behavior Tree / Blackboard contract / Gymnasium environment / PPO baseline.]

Result:
[Measured result only, or what is now testable.]

Tech:
Python, py_trees, Gymnasium, Stable-Baselines3, NumPy, pytest.
```

## Honest Phrases You Can Use After Building The Work

- "safety-first Behavior Tree"
- "Blackboard-based robot decision architecture"
- "typed decision-state validation"
- "explainable decision traces"
- "confidence-gated victim response"
- "frontier-based exploration baseline"
- "Gymnasium-compatible SAR exploration environment"
- "PPO policy benchmarked against deterministic baseline"
- "stale-data fail-safe"
- "emergency-stop override"

## Phrases To Avoid Until Actually Proven

- "real-world rescue-ready"
- "fully autonomous disaster rescue system"
- "hardware validated"
- "human detection through rubble completed"
- "production-grade robot"
- "91 percent success rate"
- "works in any disaster environment"

## Portfolio Positioning

Best title:

> Decision Logic and Explainable Autonomy for a Search-and-Rescue Robot

Best one-line description:

> Designed and implemented a safety-first Behavior Tree decision layer with explainable traces and optional RL exploration for a modular SAR robot.

Best technical bullets:

- Built a Blackboard-driven decision pipeline for modular robot integration.
- Implemented safety-priority Behavior Tree logic for emergency stop, stale data, and obstacle handling.
- Designed confidence-gated victim response using WiFi detection outputs.
- Created explainability traces mapping robot commands to behavior nodes and input facts.
- Built a deterministic exploration baseline before evaluating PPO-based exploration.

## What To Show In Screenshots Or Demos

- Behavior Tree diagram.
- Terminal output from dry-run mode.
- JSONL decision trace sample.
- Scenario test table.
- Simulator dashboard showing active behavior.
- Metrics chart comparing deterministic baseline and PPO, only after measured.

