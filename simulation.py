import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    
    # Ensure carbon_data.csv is in your root folder
    try:
        df = pd.read_csv("carbon_data.csv")
    except Exception:
        df = pd.DataFrame({"forecast": [60]*100, "actual": [65]*100})

    # Extract metrics from the 'analyze' payload
    code_impact = config.get("code_impact", {})
    energy_val = code_impact.get("energy", 0.0005)
    rating = code_impact.get("rating", "Standard")

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Medium)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    # Assign workload type based on Rating
    vms = []
    for i in range(6):
        workload = "critical" if "D" in rating else "flexible"
        vm = VM(i, workload)
        dc = dcs[i % 3]
        vm.dc = dc
        dc.vms.append(vm)
        vms.append(vm)

    migrations, delayed_tasks, total_carbon = 0, 0, 0
    logs = [f"Starting simulation for {rating} workload."]

    def process(env):
        nonlocal migrations, delayed_tasks, total_carbon
        for t in range(24):
            row = df.iloc[t % len(df)]
            trend = "increasing" if row["actual"] > row["forecast"] else "decreasing"
            
            for vm in vms:
                # Dynamic energy based on code complexity
                energy_to_use = energy_val * 100000
                vm.dc.energy_used += energy_to_use
                
                # Agent migration decision
                res = decide(vm, dcs, t, df, abs(row['forecast']-row['actual']), trend, rating)
                
                if res == "delay":
                    delayed_tasks += 1
                elif res != vm.dc:
                    vm.dc.vms.remove(vm)
                    vm.dc = res
                    res.vms.append(vm)
                    vm.last_migration_time = t
                    migrations += 1
                    logs.append(f"T={t}: VM {vm.id} moved to {res.name}")
                    
                total_carbon += vm.dc.carbon * (energy_to_use / 10)
            yield env.timeout(1)

    env.process(process(env))
    env.run()
    
    return {
        "carbon_saved": round(total_carbon * 0.15, 2),
        "migrations": migrations,
        "delayed_tasks": delayed_tasks,
        "total_credits": sum(dc.credits for dc in dcs),
        "trend": "Stable",
        "logs": logs[-10:]
    }