from app.db import DB

specs = [
    (1, 'AAH/Fish Diseases Diagnostics'),
    (2, 'AAHM'),
    (3, 'AAHM/Fish Parasitology')
]

for sid, desc in specs:
    try:
        DB.execute("INSERT INTO PA_Education_Specialization_Mst (Pk_ESP_Id, Description) VALUES (?, ?)", [sid, desc])
        print(f"Inserted: {sid} - {desc}")
    except Exception as e:
        print(f"Error inserting {desc}: {e}")
