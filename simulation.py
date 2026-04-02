def simulate(config):
    env = simpy.Environment()
    df = pd.read_csv("carbon_data.csv")

    workload_configs = config.get("workloads", []) # Now an array of 2 workloads

    dcs = [
        DataCenter("DC1 (Green)", 0.2, 1000),
        DataCenter("DC2 (Mid)", 0.5, 800),
        DataCenter("DC3 (Brown)", 0.9, 600)
    ]

    vms = []
    # Create 10 VMs: 2 from user code, 8 background noise VMs
    for i in range(10):
        if i < len(workload_configs):
            # User-defined VMs
            impact = workload_configs[i]
            vm = VM(i, "critical" if "D" in impact['rating'] else "flexible")
            vm.analyzed_energy = impact['energy']
            vm.rating = impact['rating']
        else:
            # Background noise VMs to trigger migrations
            vm = VM(i, "flexible")
            vm.analyzed_energy = 0.0001
            vm.rating = "A+"

        # Start them on the Brown DC (DC3) to force the Agent to make a choice
        dc = dcs[2] 
        vm.dc = dc
        dc.vms.append(vm)
        vms.append(vm)

    def process(env):
        nonlocal migrations
        for t in range(24):
            row = df.iloc[t % len(df)]
            for vm in vms:
                # Use the specific energy for this VM
                vm.dc.energy_used += vm.analyzed_energy * 100000
                
                # Agent Decides
                res = decide(vm, dcs, t, df, abs(row['forecast']-row['actual']), "increasing", vm.rating)
                
                if res != "delay" and res != vm.dc:
                    # Migration logic...
                    vm.dc.vms.remove(vm)
                    vm.dc = res
                    res.vms.append(vm)
                    logs.append(f"T={t}: VM {vm.id} ({vm.rating}) moved to {res.name}")
            yield env.timeout(1)