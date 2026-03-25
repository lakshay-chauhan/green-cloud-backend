def sla_risk(vm):
    return not vm.sla_ok


def carbon_high(dc):
    return dc.carbon > 0.7


def energy_exceeded(dc):
    return dc.energy_used > dc.energy_budget


def decide(vm, dcs):
    current_dc = vm.dc

    # 1️⃣ SLA PRIORITY (HIGHEST)
    if sla_risk(vm):
        # send to most powerful DC (highest energy budget)
        return max(dcs, key=lambda d: d.energy_budget)

    # 2️⃣ ENERGY CONSTRAINT
    if energy_exceeded(current_dc):
        return min(dcs, key=lambda d: d.energy_used)

    # 3️⃣ CONTROLLED DELAY (max 3 times)
    if vm.type == "flexible" and carbon_high(current_dc):
        if vm.delay_count < 3:
            vm.delay_count += 1
            return "delay"

    # 4️⃣ CARBON OPTIMIZATION
    if carbon_high(current_dc):
        return min(dcs, key=lambda d: d.carbon)

    # 5️⃣ DEFAULT: stay
    return current_dc