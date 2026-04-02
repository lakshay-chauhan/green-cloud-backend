import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    df = pd.read_csv("carbon_data.csv")

    # Metrics from the separate Analyzer service
    impact = config.get("code_impact", {})
    energy_val = impact.get("energy", 0.0005)
    rating = impact.get("rating", "Standard")

    dcs = [
        DataCenter("DC1 (Low-Carbon)", 0.2, 1000),
        DataCenter("DC2 (Mixed)", 0.5, 800),
        DataCenter("DC3 (High-Carbon)", 0.9, 600)
    ]

    # Initialize 6 VMs
    vms = [VM(i, "critical" if "D" in rating else "flexible") for i in range(6)]
    for i, vm in enumerate(vms):
        dc = dcs[i % 3]
        vm.dc = dc
        dc.vms.append(vm)

    migrations, delayed_tasks = 0, 0
    logs = [f"Simulation starting with {rating} workload footprint."]

    def process(env):
        nonlocal migrations, delayed_tasks
        for t in range(24):
            row = df.iloc[t % len(df)]
            error = abs(row["forecast"] - row["actual"])
            trend = "increasing" if row["actual"] > row["forecast"] else "decreasing"

            for vm in vms:
                # Use REAL energy analyzed by Gemini
                vm.dc.energy_used += energy_val * 100000 
                
                # Agent migration decision
                res = decide(vm, dcs, t, df, error, trend, rating)
                
                if res == "delay":
                    delayed_tasks += 1
                elif res != vm.dc:
                    vm.dc.vms.remove(vm)
                    vm.dc = res
                    res.vms.append(vm)
                    vm.last_migration_time = t
                    migrations += 1
                    logs.append(f"T={t}: Agent migrated VM {vm.id} to {res.name}")
            yield env.timeout(1)

    env.process(process(env))
    env.run()

    return {
        "migrations": migrations,
        "delayed_tasks": delayed_tasks,
        "carbon_saved": round(migrations * 2.5, 2),
        "total_credits": sum(dc.credits for dc in dcs),
        "logs": logs[-10:]
    }