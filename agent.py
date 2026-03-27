def decide(vm, dcs, current_time, df, error, trend):
    current_dc = vm.dc

    row = df.iloc[current_time % len(df)]
    forecast = row["forecast"]

    # -----------------------------
    # 1. CARBON BUDGET
    # -----------------------------
    if vm.carbon_budget <= 0:
        return min(dcs, key=lambda d: d.carbon)

    # -----------------------------
    # 2. TREND-BASED
    # -----------------------------
    if trend == "increasing":
        if current_time - vm.last_migration_time < 2:
            return current_dc   # stay

    return min(dcs, key=lambda d: d.carbon)

    if trend == "decreasing":
        if vm.type == "flexible" and vm.delay_count < 2:
            vm.delay_count += 1
            return "delay"

    # -----------------------------
    # 3. ERROR-AWARE
    # -----------------------------
    if error > 8:
        return max(dcs, key=lambda d: d.energy_budget)

    # -----------------------------
    # 4. SLA
    # -----------------------------
    if not vm.sla_ok:
        return max(dcs, key=lambda d: d.energy_budget)

    # -----------------------------
    # 5. MIGRATION COST
    # -----------------------------
    if current_time - vm.last_migration_time < 2:
        return current_dc

    # -----------------------------
    # 6. CARBON + CREDIT
    # -----------------------------
    best_dc = min(dcs, key=lambda d: (d.carbon - d.credits * 0.001))

    if forecast > 350:
        return best_dc

    return current_dc