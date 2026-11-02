from datetime import datetime, timedelta
import random
import pandas as pd

class HealthRecord:
    def __init__(self, date, weight, bcs):
        self.date = date
        self.weight = round(float(weight), 1)
        self.bcs = round(float(bcs), 2)

    def to_dict(self):
        return {"date": self.date, "weight": self.weight, "bcs": self.bcs}


class Cow:
    def __init__(self, cow_id, nickname, breed="Unknown"):
        self.id = cow_id
        self.nickname = nickname
        self.breed = breed
        self.records = []

    def add_record(self, record):
        self.records.append(record)
        self.records.sort(key=lambda r: datetime.strptime(r.date, "%Y-%m-%d"))

    def last(self):
        return self.records[-1] if self.records else None

    def to_dict(self):
        last = self.last()
        return {
            "id": self.id,
            "nickname": self.nickname,
            "breed": self.breed,
            "records": [r.to_dict() for r in self.records],
            "last_weight": last.weight if last else None,
            "last_bcs": last.bcs if last else None,
            "last_date": last.date if last else None
        }


class AlertManager:
    def __init__(self):
        self.herd = {}

    def add_cow(self, cow):
        self.herd[cow.id] = cow

    def add_record(self, cow_id, record):
        if cow_id in self.herd:
            self.herd[cow_id].add_record(record)

    def get_cow(self, cow_id):
        return self.herd.get(cow_id)

    def get_all_cows(self):
        return list(self.herd.values())

    def weight_change_percent(self, cow):
        data = sorted(cow.records, key=lambda x: x.date)
        if len(data) < 3:
            return None
        recent = data[-2:]
        prev = data[-5:-2] if len(data) >= 5 else data[:-2]
        if len(prev) < 2:
            return None
        r_w = sum(x.weight for x in recent) / len(recent)
        p_w = sum(x.weight for x in prev) / len(prev)
        return round((r_w - p_w) / p_w * 100, 1)

    def create_test_data(self):
        self.herd.clear()
        names = ["Зорька", "Буренка", "Милка", "Красавка", "Ласточка"]
        for i in range(12):
            cid = f"COW-{str(i+1).zfill(3)}"
            cow = Cow(cid, names[i % len(names)], "Голштинская")
            base_w = random.randint(550, 720)
            for d in range(8):
                date = (datetime.now() - timedelta(days=7-d)).strftime("%Y-%m-%d")
                cow.add_record(HealthRecord(date, base_w + random.uniform(-20, 25), random.uniform(2.5, 8.0)))
            self.add_cow(cow)

    def load_from_excel(self, filepath):
        df = pd.read_excel(filepath)
        self.herd.clear()

        for _, row in df.iterrows():
            cid = str(row.get('ID', '')).strip()
            if not cid:
                continue

            nickname = str(row.get('Кличка', cid)).strip()
            breed = str(row.get('Порода', 'Unknown')).strip()

            if cid not in self.herd:
                self.add_cow(Cow(cid, nickname, breed))

            # Дата
            date_val = row.get('data')
            if isinstance(date_val, (int, float)):
                date_str = (datetime(1899, 12, 30) + timedelta(days=int(date_val))).strftime("%Y-%m-%d")
            else:
                date_str = str(date_val).strip()[:10]

            weight = float(row.get('Вес', 600))
            bcs = float(row.get('BCS', 5.0))

            self.add_record(cid, HealthRecord(date_str, weight, bcs))

        print(f"Загружено коров: {len(self.herd)}")
        return True