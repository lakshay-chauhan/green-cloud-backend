import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    df = pd.read_csv("carbon_data.csv")

    # Get data from the Analyzer
    code_impact = config.get("code_impact", {})
    energy_val = code_impact.get("energy", 0.0005)
    rating = code_impact.get("rating", "B (Standard)")

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Mid)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    vms = [VM(i, "critical" if "D" in rating else "flexible") for i in range(6)]
    for i, vm in enumerate(vms):
        dc = dcs[i % 3]
        vm.dc = dc
        dc.vms.append(vm)

    migrations, delayed_tasks, total_carbon = 0, 0, 0
    logs = [f"Simulation starting for {rating} workload..."]

    def process(env):
        nonlocal migrations, delayed_tasks, total_carbon
        for t in range(24):
            row = df.iloc[t % len(df)]
            for vm in vms:
                # Use real analyzed energy
                vm.dc.energy_used += energy_val * 100000
                
                # Agent makes decision based on Rating
                res = decide(vm, dcs, t, df, abs(row['forecast']-row['actual']), "increasing", rating)
                
                if res == "delay":
                    delayed_tasks += 1
                elif res != vm.dc:
                    vm.dc.vms.remove(vm)
                    vm.dc = res
                    res.vms.append(vm)
                    migrations += 1
                    logs.append(f"T={t}: Migrated {vm.id} to {res.name}")
            yield env.timeout(1)

    env.process(process(env))
    env.run()
    return {"migrations": migrations, "delayed_tasks": delayed_tasks, "logs": logs[-10:]}