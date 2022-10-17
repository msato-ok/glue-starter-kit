import csv
import os

from faker import Faker

DATA_SIZE = 100
CSV_DIR = "fixtures/it"


def make_person():
    fake = Faker("jp-JP")

    header = [
        "UID",
        "NAME",
        "NAME_KANA",
        "ZIP",
        "ADDRESS",
        "PHONE",
        "EMAIL",
        "DATE_OF_BIRTH",
        "GENDER",
    ]
    rows = []
    for i in range(DATA_SIZE):
        row = []
        row.append("%06d" % (i + 1))
        last_name = fake.last_name_pair()
        first_name = fake.first_name_pair()
        row.append(last_name[0] + " " + first_name[0])
        row.append(last_name[1] + " " + first_name[1])
        row.append(fake.zipcode())
        row.append(fake.address())
        row.append(fake.phone_number())
        row.append(fake.email())
        row.append(fake.date_of_birth().strftime("%Y-%m-%d"))
        row.append(fake.random_element(elements=("M", "F")))
        rows.append(row)

    os.makedirs(CSV_DIR, exist_ok=True)

    with open(os.path.join(CSV_DIR, "person.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == "__main__":
    make_person()
