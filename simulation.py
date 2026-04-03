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
        "sla_violations": 0,
        "credit_penalties": 0
    }

    vms = []

    # USER TASK VMs
    for i, w in enumerate(workload_configs):
        vm_type = "critical" if "D" in w["rating"] else "flexible"

        vm = VM(i, vm_type)
        vm.energy_val = w["energy_joules"]
        vm.rating = w["rating"]
        vm.priority = 3 if "D" in w["rating"] else 1
        vm.last_migration_time = -5

        vm.dc = dcs[2]
        dcs[2].vms.append(vm)

        vms.append(vm)

    # BACKGROUND VM 1
    bg_vm1 = VM(2, "background")
    bg_vm1.energy_val = 0.02
    bg_vm1.rating = "B (Moderate)"
    bg_vm1.priority = 2
    bg_vm1.dc = dcs[1]
    dcs[1].vms.append(bg_vm1)
    vms.append(bg_vm1)

    # BACKGROUND VM 2
    bg_vm2 = VM(3, "critical")
    bg_vm2.energy_val = 0.03
    bg_vm2.rating = "D (Resource Heavy)"
    bg_vm2.priority = 3
    bg_vm2.dc = dcs[2]
    dcs[2].vms.append(bg_vm2)
    vms.append(bg_vm2)

    # INITIAL METRICS
    for vm in vms:
        stats["carbon_before"] += (
            vm.energy_val * vm.dc.carbon * 1000
        )

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
                current_dc = vm.dc

                projected_load = (
                    current_dc.energy_used
                    + vm.energy_val * 100000
                )

                # overload restriction
                if projected_load > current_dc.energy_budget:
                    vm.delay_count += 1
                    stats["sla_violations"] += 1

                    stats["logs"].append(
                        f"T={t}: VM {vm.id} delayed "
                        f"(DC overload)"
                    )
                    continue

                target = decide(
                    vm,
                    dcs,
                    t,
                    df,
                    error,
                    trend,
                    vm.rating
                )

                # migration restrictions
                if target != current_dc:
                    # credit restriction
                    if current_dc.credits < 100:
                        stats["credit_penalties"] += 1

                        stats["logs"].append(
                            f"T={t}: VM {vm.id} migration denied "
                            f"(low credits)"
                        )
                        continue

                    # cooldown
                    if t - vm.last_migration_time < 3:
                        stats["logs"].append(
                            f"T={t}: VM {vm.id} cooldown active"
                        )
                        continue

                    current_dc.vms.remove(vm)
                    target.vms.append(vm)

                    current_dc.credits -= 50
                    target.credits -= 20

                    vm.dc = target
                    vm.last_migration_time = t

                    stats["migrations"] += 1

                    stats["logs"].append(
                        f"T={t}: VM {vm.id} "
                        f"({vm.rating}) migrated "
                        f"{current_dc.name} -> {target.name} "
                        f"| credits used"
                    )

                vm.dc.energy_used += (
                    vm.energy_val * 100000
                )

                stats["carbon_after"] += (
                    vm.energy_val * vm.dc.carbon * 1000
                )

                stats["energy_after"] += vm.energy_val

            yield env.timeout(1)

    env.process(process_loop(env))
    env.run()

    carbon_saved = max(
        0,
        stats["carbon_before"]
        - stats["carbon_after"]
    )

    carbon_saved_percent = (
        round(
            carbon_saved
            / stats["carbon_before"]
            * 100,
            2
        )
        if stats["carbon_before"] > 0
        else 0
    )

    return {
        "migrations": stats["migrations"],
        "logs": stats["logs"][-20:],
        "status": "Success",

        "carbon_before": round(
            stats["carbon_before"], 4
        ),

        "carbon_after": round(
            stats["carbon_after"], 4
        ),

        "carbon_saved_percent":
            carbon_saved_percent,

        "energy_before": round(
            stats["energy_before"], 6
        ),

        "energy_after": round(
            stats["energy_after"], 6
        ),

        "sla_violations":
            stats["sla_violations"],

        "credit_penalties":
            stats["credit_penalties"],

        "dc_distribution": {
            "green": len(dcs[0].vms),
            "medium": len(dcs[1].vms),
            "brown": len(dcs[2].vms)
        }
    }