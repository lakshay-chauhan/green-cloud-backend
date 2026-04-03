import simpy
import pandas as pd
from models import DataCenter, VM
from agent import decide


def simulate(config):
    env = simpy.Environment()

    try:
        df = pd.read_csv("carbon_data.csv")
    except Exception:
        df = pd.DataFrame({
            "forecast": [50] * 48,
            "actual": [55] * 48
        })

    workload_configs = config.get("workloads", [])

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Medium)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    stats = {
        "migrations": 0,
        "logs": [],
        "carbon_before": 0,
        "carbon_after": 0,
        "energy_before": 0,
        "energy_after": 0,
        "sla_violations": 0
    }

    vms = []

    # Create VMs
    for i, w in enumerate(workload_configs):
        vm_type = "critical" if "D" in w["rating"] else "flexible"

        vm = VM(i, vm_type)
        vm.energy_val = w["energy_joules"]
        vm.rating = w["rating"]
        vm.last_migration_time = -5

        # Start from brown DC
        vm.dc = dcs[2]
        dcs[2].vms.append(vm)
        vms.append(vm)

        stats["carbon_before"] += vm.energy_val * dcs[2].carbon * 1000
        stats["energy_before"] += vm.energy_val

    def process_loop(env):
        for t in range(24):
            row = df.iloc[t % len(df)]

            error = abs(row["forecast"] - row["actual"])

            trend = (
                "increasing"
                if row["actual"] > row["forecast"]
                else "decreasing"
            )

            for vm in vms:
                vm.dc.energy_used += vm.energy_val * 100000

                target = decide(
                    vm,
                    dcs,
                    t,
                    df,
                    error,
                    trend,
                    vm.rating
                )

                if target != vm.dc:
                    old_dc = vm.dc
                    old_dc.vms.remove(vm)

                    vm.dc = target
                    target.vms.append(vm)

                    vm.last_migration_time = t

                    stats["migrations"] += 1
                    stats["logs"].append(
                        f"T={t}: VM {vm.id} ({vm.rating}) moved "
                        f"from {old_dc.name} to {target.name}"
                    )

                stats["carbon_after"] += (
                    vm.energy_val * vm.dc.carbon * 1000
                )

                stats["energy_after"] += vm.energy_val

                if vm.delay_count > 3:
                    stats["sla_violations"] += 1

            yield env.timeout(1)

    env.process(process_loop(env))
    env.run()

    carbon_saved = max(
        0,
        stats["carbon_before"] - stats["carbon_after"]
    )

    carbon_saved_percent = (
        round(
            (carbon_saved / stats["carbon_before"]) * 100,
            2
        )
        if stats["carbon_before"] > 0
        else 0
    )

    return {
        "migrations": stats["migrations"],
        "logs": stats["logs"][-20:],
        "status": "Success",
        "carbon_before": round(stats["carbon_before"], 4),
        "carbon_after": round(stats["carbon_after"], 4),
        "carbon_saved_percent": carbon_saved_percent,
        "energy_before": round(stats["energy_before"], 6),
        "energy_after": round(stats["energy_after"], 6),
        "sla_violations": stats["sla_violations"],
        "dc_distribution": {
            "green": len(dcs[0].vms),
            "medium": len(dcs[1].vms),
            "brown": len(dcs[2].vms)
        }
    }