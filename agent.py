def decide(vm, dcs, current_time, df, error, trend, sustainability_grade):
    current_dc = vm.dc
    
    # 1. Resource Heavy Override: Always move to greenest DC
    if "D" in sustainability_grade or "Heavy" in sustainability_grade:
        return min(dcs, key=lambda d: d.carbon)

    # 2. Trend-based logic
    if trend == "increasing":
        if current_time - vm.last_migration_time > 3:
            return min(dcs, key=lambda d: d.carbon)
        return current_dc

    if trend == "decreasing":
        if vm.type == "flexible" and vm.delay_count < 2:
            vm.delay_count += 1
            return "delay"

    return current_dc