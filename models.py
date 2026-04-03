class DataCenter:
    def __init__(self, name, carbon, energy_budget):
        self.name = name
        self.carbon = carbon
        self.energy_budget = energy_budget
        self.energy_used = 0

        # migration credits
        self.credits = 500

        # active VMs
        self.vms = []


class VM:
    def __init__(self, id, workload_type):
        self.id = id
        self.type = workload_type

        self.dc = None

        self.sla_ok = True
        self.sla_violated = False

        self.delay_count = 0
        self.last_migration_time = -10

        self.carbon_budget = 500

        self.energy_val = 0
        self.rating = ""

        # NEW
        self.priority = 1