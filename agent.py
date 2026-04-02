def decide(vm, dcs, current_time, df, error, trend, rating):
    current_dc = vm.dc
    
    # 1. HEAVY LOAD RULE
    # If Gemini says Task B is "D (Resource Heavy)", move it to DC1 immediately.
    if "D" in rating or "Heavy" in rating:
        return dcs[0] # DC1 (Green)

    # 2. EFFICIENCY RULE
    # If Task A is "A+ (Efficient)", let it stay unless carbon is extremely high
    if "A+" in rating:
        if current_dc.carbon > 0.7:
            return dcs[1] # Move to DC2 (Medium)
        return current_dc

    # 3. Standard Migration for others
    if trend == "increasing" and current_time - vm.last_migration_time > 3:
        return min(dcs, key=lambda d: d.carbon)

    return current_dc