import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    df = pd.read_csv("carbon_data.csv")
    workload_configs = config.get("workloads", [])

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Medium)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    # Shared state for nonlocal-safe tracking
    stats = {"migrations": 0, "total_energy_j": 0, "logs": []}

    vms = []
    # Setup VMs for the two codes entered in UI
    for i in range(len(workload_configs)):
        w = workload_configs[i]
        vm = VM(i, "critical" if "D" in w['rating'] else "flexible")
        vm.energy_val = w['energy_joules']
        vm.rating = w['rating']
        
        # Initial placement on Brown DC to force the Agent to work
        dc = dcs[2]
        vm.dc = dc
        dc.vms.append(vm)
        vms.append(vm)

    def process(env):
        for t in range(24):
            row = df.iloc[t % len(df)]
            error = abs(row["forecast"] - row["actual"])
            trend = "increasing" if row["actual"] > row["forecast"] else "decreasing"

            for vm in vms:
                # Consume Energy derived from Gemini analysis
                vm.dc.energy_used += (vm.energy_val * 100000)
                stats["total_energy_j"] += vm.energy_val
                
                target = decide(vm, dcs, t, df, error, trend, vm.rating)
                
                if target != "delay" and target != vm.dc:
                    vm.dc.vms.remove(vm)
                    vm.dc = target
                    target.vms.append(vm)
                    vm.last_migration_time = t
                    stats["migrations"] += 1
                    stats["logs"].append(f"T={t}: VM {vm.id} ({vm.rating}) moved to {target.name}")
            yield env.timeout(1)

    env.process(process(env))
    env.run()

    return {
        "migrations": stats["migrations"],
        "total_energy_joules": stats["total_energy_j"],
        "logs": stats["logs"][-15:]
    }