"""
Multi‑Agent Chaos Scenario: twee gekoppelde CORE‑instanties.
Agent A wordt langzaam chaotisch (divergerende error‑epsilon).
Agent B blijft stabiel, maar ontvangt ook de error‑epsilon van A.
Beide gebruiken dezelfde EventBus en delen elkaars toestand.
We meten:
  - Wanneer Agent B een CAUTION of hoger rapporteert, en of dat
    overeenkomt met de divergentie van A.
  - Of Agent B ten onrechte in een alarmtoestand raakt door
    overspraak (false positive).
"""

import asyncio
import json
import logging
import sys
import os
import numpy as np
from dataclasses import dataclass

# Minimaliseer logging
logging.basicConfig(level=logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))
from event_bus import EventBus, EventBusConfig
from chaos_detection import ChaosDetector, ChaosConfig, SafetyLevel

N_CYCLES = 300
DIVERGE_START = 100
SLOPE = 0.015          # agent A groeit snel
NOISE = 0.02
EPSILON_THRESHOLD = 0.5

@dataclass
class Agent:
    name: str
    detector: ChaosDetector
    epsilon_series: np.ndarray

async def main():
    # Eén gedeelde bus
    bus = EventBus(EventBusConfig(enable_persistence=False, max_queue_size=10_000))

    # Config voor beide detectoren (geen interventies)
    config = ChaosConfig(
        auto_intervene=False,
        emergency_shutdown=False,
        circuit_breaker_failures=1_000_000,
        circuit_breaker_timeout=0.0,
        prediction_horizon=5,
        epsilon_threshold=EPSILON_THRESHOLD
    )

    # Agent A: synthetische reeks met exponentiële divergentie vanaf DIVERGE_START
    t = np.arange(N_CYCLES)
    series_A = 0.1 + NOISE * np.random.randn(N_CYCLES)
    series_A[DIVERGE_START:] += SLOPE * (t[DIVERGE_START:] - DIVERGE_START) ** 2
    detector_A = ChaosDetector(config=config)

    # Agent B: stabiele reeks met kleine ruis
    series_B = 0.1 + NOISE * np.random.randn(N_CYCLES)
    detector_B = ChaosDetector(config=config)

    agent_A = Agent("A", detector_A, series_A)
    agent_B = Agent("B", detector_B, series_B)

    # Subscribers om elkaars error te delen
    # Agent A publiceert zijn error epsilon, Agent B luistert ernaar
    async def forward_error(event):
        # Agent B ontvangt error van A
        err = event.data["error"]
        metrics = {"error": err, "coherence": 0.9, "complexity": 0.5}
        await detector_B.run_safety_checks(metrics)

    bus.subscribe("agent_A_error", forward_error)

    # Agent B publiceert zijn error (voor symmetrie, maar we analyseren B's reactie op A)
    async def echo_error(event):
        pass  # in deze test niet nodig
    bus.subscribe("agent_B_error", echo_error)

    # Start bus
    await bus.start()

    # Resultaten bijhouden
    history_A = []   # (cycle, safety_level_A)
    history_B = []   # (cycle, safety_level_B)

    for cycle in range(N_CYCLES):
        # Agent A update
        val_A = series_A[cycle]
        met_A = {"error": float(val_A), "coherence": 0.9, "complexity": 0.5}
        await detector_A.run_safety_checks(met_A)
        history_A.append((cycle, detector_A.current_safety_level))

        # Agent B update (zijn eigen reeks)
        val_B = series_B[cycle]
        met_B = {"error": float(val_B), "coherence": 0.9, "complexity": 0.5}
        await detector_B.run_safety_checks(met_B)
        history_B.append((cycle, detector_B.current_safety_level))

        # A publiceert zijn error (B ontvangt via subscriber en doet extra check)
        await bus.emit("agent_A_error", {"error": float(val_A)}, source="agent_A")
        # B publiceert zijn error (niet essentieel)
        await bus.emit("agent_B_error", {"error": float(val_B)}, source="agent_B")

    await bus.stop()

    # Analyse
    # B's alarmen (safety level > NORMAL) zouden moeten optreden als A chaotisch wordt
    # maar B's eigen reeks is stabiel, dus alarmen moeten puur door overspraak komen.
    alarm_cycles_B = [c for c, lvl in history_B if lvl.value > 1]
    alarm_cycles_A = [c for c, lvl in history_A if lvl.value > 1]

    print("Multi‑Agent Chaos Experiment Resultaten:")
    print(f"Agent A (divergent): eerste alarm op cyclus {alarm_cycles_A[0] if alarm_cycles_A else 'geen'}")
    print(f"Agent B (stabiel):    eerste alarm op cyclus {alarm_cycles_B[0] if alarm_cycles_B else 'geen'}")
    print(f"Agent B totaal aantal alarmcycli: {len(alarm_cycles_B)} (van {N_CYCLES})")
    # B's eerste alarm zou na DIVERGE_START moeten liggen, maar wel later dan A's alarm
    if alarm_cycles_B and alarm_cycles_A:
        lead = alarm_cycles_B[0] - alarm_cycles_A[0]
        print(f"Agent B alarmeert {lead} cycli na Agent A (voorspelbare overspraak).")
    elif not alarm_cycles_B:
        print("Agent B bleef stabiel ondanks chaos van A: geen overspraak.")
    else:
        print("Agent B alarmeerde zonder dat A alarmeerde (onverwacht).")

    # Bewaar resultaten
    with open("multi_agent_chaos_results.json", "w") as f:
        json.dump({
            "A_first_alarm": alarm_cycles_A[0] if alarm_cycles_A else None,
            "B_first_alarm": alarm_cycles_B[0] if alarm_cycles_B else None,
            "B_total_alarms": len(alarm_cycles_B),
            "A_alarms": alarm_cycles_A,
            "B_alarms": alarm_cycles_B
        }, f, indent=2)
    print("Opgeslagen in multi_agent_chaos_results.json")

if __name__ == "__main__":
    asyncio.run(main())