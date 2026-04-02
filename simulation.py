import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide

def simulate(config):
    env = simpy.Environment()
    
    # Load carbon intensity data
    try:
        df = pd.read_csv("carbon_data.csv")
    except FileNotFoundError:
        # Fallback if CSV is missing during initial setup
        df = pd.DataFrame({"forecast": [60]*100, "actual": [60]*100})

    # ---------------------------------------------------------
    # EXTRACT ANALYZER METRICS
    # ---------------------------------------------------------
    # We pull the energy and rating sent from the React Frontend
    code_impact = config.get("code_impact", {})
    analyzed_energy = code_impact.get("energy", 0.0005) # Default small value
    sustainability_rating = code_impact.get("rating", "B (Standard)")

    # -----------------------------
    # Data Centers
    # -----------------------------
    dcs = [
        DataCenter("DC1", 0.2, 1000), # Greenest (Low Carbon)
        DataCenter("DC2", 0.5, 800),
        DataCenter("DC3", 0.9, 600)  # Brownest (High Carbon)
    ]

    # -----------------------------
    # VMs
    # -----------------------------
    vms = []
    for i in range(6):
        # We assign the workload type based on the sustainability rating
        # If the code is "Resource Heavy", we treat it as a 'critical' workload
        workload = "critical" if "Resource Heavy" in sustainability_rating else "flexible"
        
        vm = VM(i, workload)
        dc = dcs[i % len(dcs)]
        vm.dc = dc
        dc.vms.append(vm)
        vms.append(vm)

    # -----------------------------
    # Metrics Tracking
    # -----------------------------
    logs = []
    migrations = 0
    delayed_tasks = 0
    sla_violations = 0
    total_carbon = 0
    baseline_carbon = 0
    
    # Track metrics for the summary
    logs.append(f"Simulation started for code with rating: {sustainability_rating}")

    def process(env):
        nonlocal migrations, delayed_tasks, sla_violations, total_carbon, baseline_carbon
        
        while env.now < 24:  # Simulate 24 cycles
            current_time = env.now
            row = df.iloc[current_time % len(df)]
            actual_carbon = row["actual"]
            
            # Simple error/trend calculation for the agent
            error = abs(row["forecast"] - row["actual"])
            trend = "increasing" if row["actual"] > row["forecast"] else "decreasing"

            for vm in vms:
                # ---------------------------------------------------------
                # DYNAMIC ENERGY CONSUMPTION
                # ---------------------------------------------------------
                # Instead of a static '50', we use the energy from your Gemini analysis
                # We scale it (e.g., * 10^5) so it impacts the simulation budget visibly
                energy_to_consume = analyzed_energy * 100000
                vm.dc.energy_used += energy_to_consume

                # -----------------------------
                # AGENT DECISION LOGIC
                # -----------------------------
                # We pass the sustainability_rating to the agent to help it decide
                new_dc = decide(vm, dcs, current_time, df, error, trend, sustainability_rating)

                if new_dc == "delay":
                    delayed_tasks += 1
                    logs.append(f"T={current_time}: VM_{vm.id} delayed to save carbon.")
                elif new_dc != vm.dc:
                    # MIGRATION LOGIC
                    vm.dc.vms.remove(vm)
                    vm.dc = new_dc
                    new_dc.vms.append(vm)
                    vm.last_migration_time = current_time
                    migrations += 1
                    logs.append(f"T={current_time}: VM_{vm.id} migrated to {new_dc.name} due to {sustainability_rating} footprint.")

                # -----------------------------
                # CARBON & BUDGET TRACKING
                # -----------------------------
                carbon_emitted = vm.dc.carbon * (energy_to_consume / 10)
                vm.carbon_budget -= carbon_emitted
                total_carbon += carbon_emitted
                
                # Baseline assumes we stayed on the 'brownest' DC3
                baseline_carbon += dcs[2].carbon * (energy_to_consume / 10)

                # Check SLA
                if vm.dc.energy_used > vm.dc.energy_budget:
                    sla_violations += 1
                    vm.sla_ok = False

            yield env.timeout(1)

    env.process(process(env))
    env.run()

    # -----------------------------
    # FINAL METRICS
    # -----------------------------
    total_credits = sum(dc.credits for dc in dcs)
    avg_migration_cost = migrations / len(vms) if len(vms) > 0 else 0
    carbon_saved = max(baseline_carbon - total_carbon, 0)
    remaining_budget = sum(vm.carbon_budget for vm in vms)

    return {
        "carbon_saved": round(carbon_saved, 2),
        "sla_violations": sla_violations,
        "migrations": migrations,
        "delayed_tasks": delayed_tasks,
        "total_credits": total_credits,
        "avg_migration_cost": round(avg_migration_cost, 2),
        "remaining_budget": round(remaining_budget, 2),
        "trend": trend,
        "logs": logs[-15:]  # Return last 15 logs
    }