import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    
    # Safety load for CSV
    try:
        df = pd.read_csv("carbon_data.csv")
    except Exception:
        df = pd.DataFrame({"forecast": [50]*48, "actual": [55]*48})

    # Get the 2 workloads from your App.js
    workload_configs = config.get("workloads", [])

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Medium)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    # Use a dictionary for stats to avoid 'nonlocal' issues
    stats = {"migrations": 0, "logs": []}
    vms = []

    # Create VMs for your two code blocks
    for i, w in enumerate(workload_configs):
        # Assign "critical" if D rating to show it needs high-availability green power
        vm_type = "critical" if "D" in w['rating'] else "flexible"
        vm = VM(i, vm_type)
        vm.energy_val = w['energy_joules']
        vm.rating = w['rating']
        vm.last_migration_time = -5
        
        # Start both on the Brown DC (DC3) so the agent is forced to migrate them
        vm.dc = dcs[2]
        dcs[2].vms.append(vm)
        vms.append(vm)

    def process_loop(env):
        for t in range(24):
            row = df.iloc[t % len(df)]
            error = abs(row["forecast"] - row["actual"])
            trend = "increasing" if row["actual"] > row["forecast"] else "decreasing"
            
            for vm in vms:
                # Real physical consumption
                vm.dc.energy_used += (vm.energy_val * 100000)
                
                # Agent migration logic
                target = decide(vm, dcs, t, df, error, trend, vm.rating)
                
                if target != "delay" and target != vm.dc:
                    vm.dc.vms.remove(vm)
                    vm.dc = target
                    target.vms.append(vm)
                    vm.last_migration_time = t
                    stats["migrations"] += 1
                    stats["logs"].append(f"T={t}: VM {vm.id} ({vm.rating}) moved to {target.name}")
            yield env.timeout(1)

    env.process(process_loop(env))
    env.run()
    
    return {
        "migrations": stats["migrations"],
        "logs": stats["logs"][-20:], # Send last 20 logs to UI
        "status": "Success"
    }