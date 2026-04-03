import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    
    # ✅ Safety check for CSV
    try:
        df = pd.read_csv("carbon_data.csv")
    except:
        df = pd.DataFrame({"forecast": [50]*48, "actual": [55]*48})

    workloads = config.get("workloads", [])
    dcs = [DataCenter("DC1 (Green)", 0.2, 1000), DataCenter("DC2 (Mid)", 0.5, 800), DataCenter("DC3 (Brown)", 0.9, 600)]

    # Use a dict to store state (prevents 'nonlocal' errors)
    stats = {"migrations": 0, "logs": []}
    vms = []

    for i, w in enumerate(workloads):
        vm = VM(i, "critical" if "D" in w['rating'] else "flexible")
        vm.energy_val = w['energy_joules']
        vm.rating = w['rating']
        vm.last_migration_time = -5
        
        # Start on DC3 (Brown)
        vm.dc = dcs[2]
        dcs[2].vms.append(vm)
        vms.append(vm)

    def process_loop(env):
        for t in range(24):
            row = df.iloc[t % len(df)]
            trend = "increasing" if row["actual"] > row["forecast"] else "decreasing"
            
            for vm in vms:
                vm.dc.energy_used += (vm.energy_val * 100000)
                target = decide(vm, dcs, t, df, abs(row["actual"]-row["forecast"]), trend, vm.rating)
                
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
    return {"migrations": stats["migrations"], "logs": stats["logs"][-15:]}