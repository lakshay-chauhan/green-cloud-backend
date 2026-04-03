def decide(vm, dcs, current_time, df, error, trend, rating):
    current_dc = vm.dc

    if "D" in rating or "Heavy" in rating:
        return dcs[0]

    if "A+" in rating:
        if current_dc.carbon > 0.7:
            return dcs[1]
        return current_dc

    if trend == "increasing" and current_time - vm.last_migration_time > 3:
        return min(dcs, key=lambda d: d.carbon)

    return current_dc