import simpy
from models import DataCenter, VM
from agent import decide


def simulate(config):
    env = simpy.Environment()

    # -----------------------------
    # Create Data Centers
    # -----------------------------
    dcs = [
        DataCenter("DC1", carbon=0.2, energy_budget=1000),
        DataCenter("DC2", carbon=0.5, energy_budget=800),
        DataCenter("DC3", carbon=0.9, energy_budget=600)
    ]

    # -----------------------------
    # Create VMs
    # -----------------------------
    vms = []
    for i in range(6):
        vm_type = "flexible" if i % 2 == 0 else "critical"
        vm = VM(i, vm_type)

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

    # -----------------------------
    # Simulation Process
    # -----------------------------
    def process(env):
        nonlocal migrations, delayed_tasks, sla_violations
        nonlocal total_carbon, baseline_carbon

        while env.now < 10:

            for vm in vms:

                current_dc = vm.dc

                # -----------------------------
                # SLA CHECK (FIXED)
                # -----------------------------
                if current_dc.energy_used > current_dc.energy_budget * 0.8:
                    vm.sla_ok = False

                    if not vm.sla_violated:
                        sla_violations += 1
                        vm.sla_violated = True
                else:
                    vm.sla_ok = True
                    vm.sla_violated = False

                # -----------------------------
                # Baseline carbon (no optimization)
                # -----------------------------
                baseline_carbon += current_dc.carbon * 10

                # -----------------------------
                # Decision Making
                # -----------------------------
                decision = decide(vm, dcs)

                # -----------------------------
                # Delay Handling
                # -----------------------------
                if decision == "delay":
                    delayed_tasks += 1
                    logs.append(
                        f"Time {env.now}: VM{vm.id} delayed (carbon high in {current_dc.name})"
                    )
                    continue

                # -----------------------------
                # Migration Handling
                # -----------------------------
                if decision != current_dc:
                    logs.append(
                        f"Time {env.now}: VM{vm.id} moved {current_dc.name} → {decision.name}"
                    )

                    current_dc.vms.remove(vm)
                    vm.dc = decision
                    decision.vms.append(vm)

                    migrations += 1

                # -----------------------------
                # Energy Usage
                # -----------------------------
                vm.dc.energy_used += 50

                # -----------------------------
                # Actual carbon usage
                # -----------------------------
                total_carbon += vm.dc.carbon * 10

                # -----------------------------
                # Carbon Credits (optional logic)
                # -----------------------------
                if vm.dc.carbon < 0.5:
                    vm.dc.credits += 5
                else:
                    vm.dc.credits -= 5

            yield env.timeout(1)

    # Run simulation
    env.process(process(env))
    env.run()

    # -----------------------------
    # Final Metrics
    # -----------------------------
    carbon_saved = max(baseline_carbon - total_carbon, 0)

    return {
        "carbon_saved": round(carbon_saved, 2),
        "sla_violations": sla_violations,
        "migrations": migrations,
        "delayed_tasks": delayed_tasks,
        "logs": logs
    }