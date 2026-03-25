class DataCenter:
    def __init__(self, name, carbon, energy_budget):
        self.name = name
        self.carbon = carbon
        self.energy_budget = energy_budget
        self.energy_used = 0
        self.credits = 500
        self.vms = []


class VM:
    def __init__(self, id, workload_type):
        self.id = id
        self.type = workload_type  # "critical" or "flexible"
        self.dc = None
        self.sla_ok = True
        self.sla_violated = False  # ✅ FIXED (prevents duplicate counting)
        self.delay_count = 0       # ✅ FIXED (controls delay loop)