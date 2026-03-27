import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide


def simulate(config):
    env = simpy.Environment()
    df = pd.read_csv("carbon_data.csv")

    # -----------------------------
    # Data Centers
    # -----------------------------
    dcs = [
        DataCenter("DC1", 0.2, 1000),
        DataCenter("DC2", 0.5, 800),
        DataCenter("DC3", 0.9, 600)
    ]

    # -----------------------------
    # VMs
    # -----------------------------
    vms = []
    for i in range(6):
        vm = VM(i, "flexible" if i % 2 == 0 else "critical")
        dc = dcs[i % len(dcs)]
        vm.dc = dc
        dc.vms.append(vm)
        vms.append(vm)

    # -----------------------------
    # Metrics
    # -----------------------------
    logs = []
    migrations = 0
    delayed_tasks = 0
    sla_violations = 0

    total_carbon = 0
    baseline_carbon = 0

    carbon_history = []

    # 🔥 FIX: declare trend globally
    final_trend = "stable"

    # -----------------------------
    # Simulation Process
    # -----------------------------
    def process(env):
        nonlocal migrations, delayed_tasks, sla_violations
        nonlocal total_carbon, baseline_carbon
        nonlocal final_trend   # ✅ IMPORTANT FIX

        while env.now < 10:
            row = df.iloc[env.now % len(df)]

            forecast = row["forecast"]
            actual = row["actual"]

            carbon_history.append(forecast)

            # -----------------------------
            # TREND DETECTION
            # -----------------------------
            if len(carbon_history) >= 2:
                if carbon_history[-1] > carbon_history[-2]:
                    final_trend = "increasing"
                elif carbon_history[-1] < carbon_history[-2]:
                    final_trend = "decreasing"
                else:
                    final_trend = "stable"
            else:
                final_trend = "stable"

            logs.append(f"Time {env.now}: Trend={final_trend}")

            # -----------------------------
            # UPDATE DC CARBON
            # -----------------------------
            for i, dc in enumerate(dcs):
                dc.carbon = df.iloc[(env.now + i) % len(df)]["forecast"] / 500

            # -----------------------------
            # ERROR
            # -----------------------------
            error = abs(actual - forecast)

            logs.append(
                f"Time {env.now}: Forecast={forecast}, Actual={actual}, Error={error}"
            )

            # -----------------------------
            # PROCESS VMs
            # -----------------------------
            for vm in vms:
                current_dc = vm.dc

                # SLA CHECK
                if current_dc.energy_used > current_dc.energy_budget * 0.8:
                    vm.sla_ok = False
                    sla_violations += 1
                else:
                    vm.sla_ok = True

                baseline_carbon += current_dc.carbon * 10

                # DECISION
                decision = decide(vm, dcs, env.now, df, error, final_trend)

                # DELAY
                if decision == "delay":
                    delayed_tasks += 1
                    logs.append(f"Time {env.now}: VM{vm.id} delayed")
                    continue

                # MIGRATION
                if decision != current_dc:
                    logs.append(
                        f"Time {env.now}: VM{vm.id} moved {current_dc.name} → {decision.name}"
                    )

                    current_dc.vms.remove(vm)
                    vm.dc = decision
                    decision.vms.append(vm)

                    vm.last_migration_time = env.now
                    migrations += 1

                # ENERGY
                vm.dc.energy_used += 50

                # -----------------------------
                # CARBON BUDGET
                # -----------------------------
                vm.carbon_budget -= vm.dc.carbon * 10

                # TRACK CARBON
                total_carbon += vm.dc.carbon * 10

                # -----------------------------
                # CREDIT SYSTEM
                # -----------------------------
                if vm.dc.carbon < 0.4:
                    vm.dc.credits += 10
                else:
                    vm.dc.credits -= 5

            yield env.timeout(1)

    env.process(process(env))
    env.run()

    # -----------------------------
    # FINAL METRICS
    # -----------------------------
    total_credits = sum(dc.credits for dc in dcs)

    avg_migration_cost = migrations / len(vms) if len(vms) > 0 else 0

    total_remaining_budget = sum(vm.carbon_budget for vm in vms)

    carbon_saved = max(baseline_carbon - total_carbon, 0)

    return {
        "carbon_saved": round(carbon_saved, 2),
        "sla_violations": sla_violations,
        "migrations": migrations,
        "delayed_tasks": delayed_tasks,
        "total_credits": total_credits,
        "avg_migration_cost": round(avg_migration_cost, 2),
        "remaining_budget": round(total_remaining_budget, 2),
        "trend": final_trend,
        "logs": logs
    }