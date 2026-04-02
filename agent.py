def decide(vm, dcs, current_time, df, error, trend, rating):
    # Rule: If VM is Grade D (Heavy), move it to DC1 (Green) immediately
    if "D" in rating:
        return dcs[0] # DC1

    # Rule: If VM is Grade A+ (Efficient), it can stay on DC2 to save migration costs
    if "A+" in rating:
        if vm.dc.carbon > 0.6: # If current DC is too dirty
            return dcs[1] # Move to Mid-range DC
        return vm.dc

    return min(dcs, key=lambda d: d.carbon)