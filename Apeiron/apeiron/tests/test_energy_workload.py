"""
Energy & CO₂ benchmark for the Apeiron Core.

Trains a ResNet‑18 on CIFAR‑10 for 1 epoch, measures energy (J) and CO₂ (g)
per batch using ThermodynamicCost, for CPU and GPU, under BALANCED and GREEN
priority. Runs each configuration 3 times and saves statistics to
energy_results.json.
"""

import sys, os, json, time, asyncio
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.thermodynamic_cost import ThermodynamicCost, CostPriority, CostConfig

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
BATCH_SIZE = 64
N_EPOCHS = 1
N_RUNS = 3

DEVICES = ['cpu', 'cuda'] if torch.cuda.is_available() else ['cpu']
PRIORITIES = [CostPriority.BALANCED, CostPriority.GREEN]

MODEL_NAME = 'ResNet‑18'
DATASET = 'CIFAR‑10'
INFORMATION_VALUE = 0.8     # proxy for useful computation

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def create_dataloader():
    transform = transforms.Compose([transforms.ToTensor()])
    trainset = torchvision.datasets.CIFAR10(
        root='./data', train=True, download=True, transform=transform)
    return torch.utils.data.DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=True)

async def run_workload(device_str, priority):
    """Run the training and return total energy, CO2, wall time, and efficiency."""
    cost = ThermodynamicCost(
        CostConfig(
            priority=priority,
            energy_budget=1_000_000,        # unlimited for this test
            enable_co2_tracking=True,
            enable_predictive=False,
            enable_dynamic_pricing=False,
            monitoring_interval=0.1
        )
    )

    # Override the internal monitor to use real hardware but skip API calls
    # (the monitor already uses psutil/NVML, we just disable API)
    cost.co2_client.api_key = None

    dataloader = create_dataloader()
    model = torchvision.models.resnet18(pretrained=False).to(device_str)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    total_energy = 0.0
    total_co2 = 0.0
    start_wall = time.time()

    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device_str), labels.to(device_str)
        t0 = time.perf_counter()
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        elapsed = time.perf_counter() - t0

        # Evaluate this batch
        approved, info = await cost.evaluate(
            structure_id="batch",
            computation_time=elapsed,
            information_value=INFORMATION_VALUE
        )
        total_energy += info.energy_joules
        total_co2 += info.co2_grams

    wall_time = time.time() - start_wall
    avg_efficiency = INFORMATION_VALUE / (total_energy / len(dataloader) + 1e-10)

    return {
        'total_energy_joules': total_energy,
        'total_co2_grams': total_co2,
        'wall_time_s': wall_time,
        'avg_efficiency': avg_efficiency
    }

async def main():
    results = {}
    for device in DEVICES:
        for priority in PRIORITIES:
            key = f"{device}_{priority.name}"
            runs = []
            print(f"\nRunning {key} ({N_RUNS} runs)...")
            for run in range(N_RUNS):
                print(f"  Run {run+1}/{N_RUNS}")
                metrics = await run_workload(device, priority)
                runs.append(metrics)

            # Aggregate
            aggregated = {
                'energy_mean': np.mean([r['total_energy_joules'] for r in runs]),
                'energy_std': np.std([r['total_energy_joules'] for r in runs]),
                'co2_mean': np.mean([r['total_co2_grams'] for r in runs]),
                'co2_std': np.std([r['total_co2_grams'] for r in runs]),
                'wall_time_mean': np.mean([r['wall_time_s'] for r in runs]),
                'wall_time_std': np.std([r['wall_time_s'] for r in runs]),
                'efficiency_mean': np.mean([r['avg_efficiency'] for r in runs]),
                'efficiency_std': np.std([r['avg_efficiency'] for r in runs]),
                'raw_runs': runs
            }
            results[key] = aggregated

    # Save
    with open('energy_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\nEnergy Benchmark Summary")
    print("=" * 80)
    for key, stats in results.items():
        print(f"{key}:")
        print(f"  Energy: {stats['energy_mean']:.0f} ± {stats['energy_std']:.0f} J")
        print(f"  CO₂:    {stats['co2_mean']:.2f} ± {stats['co2_std']:.2f} g")
        print(f"  Time:   {stats['wall_time_mean']:.1f} ± {stats['wall_time_std']:.1f} s")
        print(f"  Efficiency: {stats['efficiency_mean']:.4f} ± {stats['efficiency_std']:.4f}")
    print("Saved to energy_results.json")

if __name__ == "__main__":
    asyncio.run(main())