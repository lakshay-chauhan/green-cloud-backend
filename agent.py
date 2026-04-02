def decide(vm, dcs, current_time, df, error, trend, sustainability_grade):
    """
    Intelligent Agent Decision Logic:
    Decides whether to stay, migrate, or delay based on carbon trends, 
    SLA status, and the analyzed Sustainability Rating of the code.
    """
    current_dc = vm.dc
    row = df.iloc[current_time % len(df)]
    
    # ---------------------------------------------------------
    # 1. CRITICAL OVERRIDE: HEAVY CODE FOOTPRINT
    # ---------------------------------------------------------
    # If Gemini analyzed the code as "Resource Heavy", we don't delay it.
    # Instead, we force it to the greenest available DC (DC1) to mitigate impact.
    if "Resource Heavy" in sustainability_grade or "D" in sustainability_grade:
        greenest_dc = min(dcs, key=lambda d: d.carbon)
        if current_dc != greenest_dc:
            return greenest_dc
        return current_dc

    # ---------------------------------------------------------
    # 2. CARBON BUDGET PROTECTION
    # ---------------------------------------------------------
    # If the VM is running out of carbon credits, move to the greenest DC
    if vm.carbon_budget <= 10:
        return min(dcs, key=lambda d: d.carbon)

    # ---------------------------------------------------------
    # 3. TREND-BASED MIGRATION (Increasing Carbon)
    # ---------------------------------------------------------
    if trend == "increasing":
        # If carbon is rising, move to a DC with lower intensity
        # But avoid 'thrashing' (migrating too frequently)
        if current_time - vm.last_migration_time > 3:
            target_dc = min(dcs, key=lambda d: d.carbon)
            return target_dc
        return current_dc

    # ---------------------------------------------------------
    # 4. OPPORTUNISTIC DELAY (Decreasing Carbon)
    # ---------------------------------------------------------
    if trend == "decreasing":
        # If code is 'flexible' and carbon is currently high but dropping, 
        # we delay the task to wait for cleaner energy.
        if vm.type == "flexible" and vm.delay_count < 2:
            vm.delay_count += 1
            return "delay"

    # ---------------------------------------------------------
    # 5. ERROR-AWARE LOAD BALANCING
    # ---------------------------------------------------------
    # If the forecast error is high (unreliable grid), move to a DC 
    # with a larger energy budget to prevent SLA violations.
    if error > 10:
        return max(dcs, key=lambda d: d.energy_budget)

    # ---------------------------------------------------------
    # 6. SLA RECOVERY
    # ---------------------------------------------------------
    # If a DC is over-budget (SLA violated), move the VM out
    if not vm.sla_ok or current_dc.energy_used > current_dc.energy_budget:
        # Move to the DC with the most remaining capacity
        return max(dcs, key=lambda d: d.energy_budget - d.energy_used)

    # Default: Stay on current DC
    return current_dc