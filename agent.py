def decide(vm, dcs, current_time, df, error, trend, rating):
    current_dc = vm.dc

    # High priority heavy tasks → always prefer green DC
    if "D" in rating or "Heavy" in rating:
        green_dc = dcs[0]

        # if already on green stay
        if current_dc == green_dc:
            return current_dc

        # migrate only if credits available
        if current_dc.credits >= 100:
            return green_dc

        return current_dc

    # Efficient tasks
    if "A+" in rating:
        # only move if current carbon is very high
        if current_dc.carbon > 0.7:
            return dcs[1]

        return current_dc

    # Moderate tasks
    if "B" in rating:
        # migrate only if carbon trend worsens
        if trend == "increasing":
            return min(dcs, key=lambda d: d.carbon)

    # cooldown protection
    if current_time - vm.last_migration_time < 3:
        return current_dc

    return current_dc