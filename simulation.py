import simpy
                if row["actual"] > row["forecast"]
                else "decreasing"
            )

            for vm in vms:
                vm.dc.energy_used += vm.energy_val * 100000

                target = decide(vm, dcs, t, df, error, trend, vm.rating)

                if target != "delay" and target != vm.dc:
                    old_dc = vm.dc
                    old_dc.vms.remove(vm)

                    vm.dc = target
                    target.vms.append(vm)
                    vm.last_migration_time = t

                    stats["migrations"] += 1
                    stats["logs"].append(
                        f"T={t}: VM {vm.id} ({vm.rating}) migrated from {old_dc.name} to {target.name}"
                    )

                stats["carbon_after"] += vm.energy_val * vm.dc.carbon * 1000
                stats["energy_after"] += vm.energy_val

                if vm.delay_count > 3:
                    stats["sla_violations"] += 1

            yield env.timeout(1)

    env.process(process_loop(env))
    env.run()

    carbon_saved = max(
        0,
        stats["carbon_before"] - stats["carbon_after"],
    )

    carbon_saved_percent = (
        round((carbon_saved / stats["carbon_before"]) * 100, 2)
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
            "brown": len(dcs[2].vms),
        },
    }