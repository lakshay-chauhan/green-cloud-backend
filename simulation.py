import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    df = pd.read_csv("carbon_data.csv")
    
    # Get workloads from payload
    workload_configs = config.get("workloads", [])

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Medium)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    # Tracking variables defined in simulate() scope
    vars_dict = {
        "migrations": 0,
        "logs": []
    }

    vms = []
    # Create 8 VMs: First 2 are user-defined, others are noise
    for i in range(8):
        if i < len(workload_configs):
            impact = workload_configs[i]
            vm = VM(i, "critical" if "D" in impact['rating'] else "flexible")
            vm.analyzed_energy = impact['energy']
            vm.rating = impact['rating']
        else:
            vm = VM(i, "flexible")
            vm.analyzed_energy = 0.0001
            vm.rating = "A+ (Efficient)"

        # Start everything on DC3 (Brown) to force migrations
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
                # Dynamic Energy Consumption
                vm.dc.energy_used += vm.analyzed_energy * 100000
                
                # Agent Decision
                target_dc = decide(vm, dcs, t, df, error, trend, vm.rating)
                
                if target_dc != "delay" and target_dc != vm.dc:
                    # Perform Migration
                    vm.dc.vms.remove(vm)
                    vm.dc = target_dc
                    target_dc.vms.append(vm)
                    vm.last_migration_time = t
                    vars_dict["migrations"] += 1
                    vars_dict["logs"].append(f"T={t}: VM {vm.id} ({vm.rating}) moved to {target_dc.name}")
            
            yield env.timeout(1)

    env.process(process(env))
    env.run()

    return {
        "migrations": vars_dict["migrations"],
        "logs": vars_dict["logs"][-15:],
        "carbon_saved": round(vars_dict["migrations"] * 1.8, 2)
    }