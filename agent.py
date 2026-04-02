def decide(vm, dcs, current_time, df, error, trend, rating):
    current_dc = vm.dc
    
    # Priority 1: If Gemini says it's heavy, force it to DC1 (Greenest)
    if "D" in rating or "Heavy" in rating:
        greenest = min(dcs, key=lambda d: d.carbon)
        return greenest

    # Priority 2: Trend Handling
    if trend == "increasing" and current_time - vm.last_migration_time > 3:
        return min(dcs, key=lambda d: d.carbon)

    # Priority 3: Delay flexible tasks if carbon is dropping later
    if trend == "decreasing" and vm.type == "flexible" and vm.delay_count < 2:
        vm.delay_count += 1
        return "delay"

    return current_dc