import simpy
import random
import numpy as np

# --- DAĞILIM PARAMETRELERİ  ---
# Gamma: alpha = mean^2 / std^2, beta = std^2 / mean
dist_params = {
    "pin": (338.7, 0.0051),
    "body": (465.0, 0.0148),
    "welding": (2.01, 0.188),    # Lognormal (mu, sigma)
    "assembly": (2.44, 0.116),   # Lognormal (mu, sigma)
    "packaging": (1.62, 0.38)    # Lognormal (mu, sigma)
}

class Fabrika:
    def __init__(self, env):
        self.env = env
        # Makineler 
        self.doorbolt_body = simpy.Resource(env, capacity=1)
        self.doorbolt_pin = simpy.Resource(env, capacity=1)
        self.triple_bead = simpy.Resource(env, capacity=6)
        self.welding_machine = simpy.Resource(env, capacity=1)
        self.assembly_area = simpy.Resource(env, capacity=5) 
        
        # Parça Depoları (Store)
        self.pin_depo = simpy.Store(env)
        self.body_depo = simpy.Store(env)
        self.bead_depo = simpy.Store(env)
        self.welded_part_depo = simpy.Store(env)

    # 1. Pim Üretim Süreci
    def pin_uretim(self):
        while True:
            with self.doorbolt_pin.request() as req:
                yield req
                süre = random.gammavariate(*dist_params["pin"])
                yield self.env.timeout(süre)
                yield self.pin_depo.put("Pim")

    # 2. Gövde Üretim Süreci
    def body_uretim(self):
        while True:
            with self.doorbolt_body.request() as req:
                yield req
                süre = random.gammavariate(*dist_params["body"])
                yield self.env.timeout(süre)
                yield self.body_depo.put("Gövde")

    # 3. Kaynak Süreci (Gövde + Boncuk birleşimi)
    def welding_process(self):
        while True:
            body = yield self.body_depo.get()
            # Boncuk üretimini burada bekleyebilir veya ayrı process yapabiliriz
            with self.welding_machine.request() as req:
                yield req
                süre = random.lognormvariate(*dist_params["welding"])
                yield self.env.timeout(süre)
                yield self.welded_part_depo.put("Kaynaklı Gövde")

    # 4. Final Montaj (Kaynaklı Gövde + Pim)
    def assembly_process(self):
        while True:
            welded = yield self.welded_part_depo.get()
            pin = yield self.pin_depo.get() # İkisi de hazır olunca başlar
            with self.assembly_area.request() as req:
                yield req
                süre = random.lognormvariate(*dist_params["assembly"])
                yield self.env.timeout(süre)
                print(f"Sürgü Tamamlandı: {self.env.now:.2f}")

# Simülasyonu Başlat
env = simpy.Environment()
horoz_demir = Fabrika(env)

env.process(horoz_demir.pin_uretim())
env.process(horoz_demir.body_uretim())
env.process(horoz_demir.welding_process())
env.process(horoz_demir.assembly_process())

env.run(until=3600) # 1 saatlik üretim