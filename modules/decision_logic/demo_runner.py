# modules/decision_logic/demo_runner.py
#
# ┌──────────────────────────────────────────────────────────────────┐
# │           PROJECT DRISHYA — Brain Module Demo Runner             │
# │                 Mid-Term Defense Showpiece                       │
# └──────────────────────────────────────────────────────────────────┘
#
# Runs the full Behavior Tree + RL decision system in the terminal,
# cycling through different scenarios every 6 seconds so supervisors
# can see each BT node activate in real time.
#
# Run from project root:
#   python -m modules.decision_logic.demo_runner
#
# What it demonstrates:
#   ✓ Behavior Tree ticking at 10 Hz
#   ✓ Priority Selector: Safety → Victim → Navigate → RL Explore → Idle
#   ✓ Automatic scenario transitions with live state updates
#   ✓ Motor command output written to the Blackboard
#   ✓ Exploration percentage counter (RL node)
#   ✓ Emergency stop triggering and clearing

import sys
import os
import time

# ── make project root importable ──────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.blackboard       import Blackboard
from modules.decision_logic.demo_data import get_mock_detection, get_mock_nav_state
from modules.decision_logic.brain import Brain
from modules.decision_logic.contracts import MISSION_CONTROL, PROXIMITY, ROBOT_POSE, now_ms

# ── ANSI colour helpers ────────────────────────────────────────────────────────
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

def _colour_status(status: str) -> str:
    """Apply colour to BT status string based on active node."""
    if "EMERGENCY"  in status: return f"{RED}{BOLD}{status}{RESET}"
    if "VICTIM"     in status: return f"{MAGENTA}{BOLD}{status}{RESET}"
    if "NAVIGATING" in status: return f"{BLUE}{status}{RESET}"
    if "RL_EXPLORE" in status: return f"{GREEN}{status}{RESET}"
    if "ARRIVED"    in status: return f"{CYAN}{status}{RESET}"
    if "IDLE"       in status: return f"{DIM}{status}{RESET}"
    return f"{WHITE}{status}{RESET}"

def _colour_motor(cmd: dict) -> str:
    if not cmd:
        return f"{DIM}no command{RESET}"
    L = cmd.get("left_speed",  0)
    R = cmd.get("right_speed", 0)
    d = cmd.get("duration_ms", 0)
    if L == 0 and R == 0:
        colour = RED if d == 0 else YELLOW
    elif L == R:
        colour = GREEN
    else:
        colour = CYAN
    return f"{colour}L={L:+4d}  R={R:+4d}  t={d}ms{RESET}"


# ── Scenario playlist ──────────────────────────────────────────────────────────
# Each entry: (nav_scenario, detection_scenario, description, hold_seconds)
PLAYLIST = [
    # 1. Robot just powered on — no data, falls to Idle
    ("start",          "no_human",        "🔵  BOOT  │ No sensors yet  →  Idle",           4),
    # 2. Exploring — RL policy drives exploration
    ("exploring",      "no_human",        "🟢  EXPLORE  │ RL policy searching the map",     6),
    # 3. Weak WiFi signal — still exploring (confidence below threshold)
    ("exploring",      "weak_signal",     "🟡  WEAK SIGNAL  │ conf=0.52, keep exploring",   5),
    # 4. OBSTACLE! Emergency stop fires
    ("obstacle_ahead", "no_human",        "🔴  EMERGENCY STOP  │ obstacle < 15 cm",         5),
    # 5. Obstacle cleared, strong detection arrives
    ("exploring",      "strong_detection","🟣  VICTIM CONFIRMED  │ conf=0.91 → set waypoint",5),
    # 6. Navigate to waypoint
    ("target_locked",  "strong_detection","🔷  NAVIGATING  │ steering toward victim",       6),
    # 7. Near victim — confirm arrival
    ("near_victim",    "strong_detection","✅  ARRIVED  │ victim located, mission success",  5),
    # 8. Loop back to exploration
    ("exploring",      "no_human",        "🟢  EXPLORE  │ continuing map coverage",         5),
]


def _load_scenario(bb: Blackboard, nav_sc: str, det_sc: str):
    """Push a new scenario into the Blackboard."""
    nav = get_mock_nav_state(nav_sc)
    det = get_mock_detection(det_sc)

    bb.set("navigation/robot_pose",      nav["robot_pose"])
    bb.set("navigation/occupancy_grid",  nav["occupancy_grid"])
    bb.set("navigation/planned_path",    nav["planned_path"])
    bb.set("navigation/target_waypoint", nav["target_waypoint"])
    bb.set("sensor/proximity",           nav["proximity"])
    bb.set("detection/result",           det)
    bb.set(MISSION_CONTROL, {
        "mode": "idle" if nav_sc == "start" else "run",
        "emergency_stop": False,
        "timestamp_ms": now_ms(),
    })


def _refresh_runtime_state(bb: Blackboard):
    """Emulate live navigation/sensor publishers during the terminal demo."""
    timestamp_ms = now_ms()
    pose = dict(bb.get(ROBOT_POSE, {}))
    proximity = dict(bb.get(PROXIMITY, {}))
    pose["timestamp_ms"] = timestamp_ms
    proximity["timestamp_ms"] = timestamp_ms
    bb.set(ROBOT_POSE, pose)
    bb.set(PROXIMITY, proximity)


def _header():
    w = 72
    print(f"\n{BOLD}{'═' * w}{RESET}")
    print(f"{BOLD}{'PROJECT DRISHYA — Brain Module Live Demo':^{w}}{RESET}")
    print(f"{BOLD}{'Behavior Tree + Reinforcement Learning Decision System':^{w}}{RESET}")
    print(f"{BOLD}{'═' * w}{RESET}\n")

    print(f"  {BOLD}Behavior Tree Priority Order:{RESET}")
    print(f"    {RED}1. EmergencyStop{RESET}      ← Obstacle < 15 cm")
    print(f"    {MAGENTA}2. VictimConfirmation{RESET} ← WiFi confidence ≥ 0.85")
    print(f"    {BLUE}3. NavigateToTarget{RESET}   ← Active waypoint set")
    print(f"    {GREEN}4. RLExplore (PPO){RESET}    ← Explore unknown cells")
    print(f"    {DIM}5. Idle{RESET}               ← Fallback")
    print(f"\n  {DIM}Ticking at 10 Hz  |  Ctrl+C to stop{RESET}\n")
    print("─" * w)


def main():
    _header()
    bb    = Blackboard()
    brain = Brain(bb)
    brain.start()

    total_duration = sum(h for _, _, _, h in PLAYLIST)
    elapsed_total  = 0

    try:
        for nav_sc, det_sc, description, hold in PLAYLIST:
            _load_scenario(bb, nav_sc, det_sc)

            print(f"\n  {BOLD}SCENARIO:{RESET}  {description}")
            print(f"  {DIM}Nav={nav_sc}  Det={det_sc}  Duration={hold}s{RESET}")
            print("  " + "·" * 66)

            t_end = time.time() + hold
            tick  = 0

            while time.time() < t_end:
                _refresh_runtime_state(bb)
                time.sleep(0.1)
                tick += 1

                if tick % 3 != 0:     # print every ~0.3s (don't spam)
                    continue

                bt_status  = bb.get("state/bt_status", "– waiting –")
                motor_cmd  = bb.get("state/motor_command", {})
                detection  = bb.get("detection/result", {})
                proximity  = bb.get("sensor/proximity", {})

                conf = detection.get("confidence", 0.0) if detection else 0.0
                prox_front = proximity.get("us_front", 0) if proximity else 0

                elapsed_total += 0.1
                progress = elapsed_total / total_duration
                bar_w    = 30
                filled   = int(bar_w * min(progress, 1.0))
                bar      = f"[{'█' * filled}{'░' * (bar_w - filled)}]"

                print(
                    f"  {DIM}{bar}{RESET}  "
                    f"BT: {_colour_status(bt_status):<70}  "
                    f"Motor: {_colour_motor(motor_cmd)}  "
                    f"conf={YELLOW}{conf:.2f}{RESET}  "
                    f"front={RED if prox_front < 15 else WHITE}{prox_front}cm{RESET}"
                )

    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Demo interrupted by user.{RESET}")

    finally:
        brain.stop()
        print(f"\n{'─' * 72}")
        print(f"  {BOLD}Demo complete.{RESET}  Total BT ticks: {BOLD}{brain._tick_count}{RESET}")
        print(f"  Model:  {os.path.join('modules/decision_logic/models/', 'ppo_sar_explore.zip')}")
        print(f"  Brain:  {brain._tick_count} ticks @ 10 Hz = "
              f"~{brain._tick_count / 10:.0f}s runtime")
        print("═" * 72 + "\n")


if __name__ == "__main__":
    main()
