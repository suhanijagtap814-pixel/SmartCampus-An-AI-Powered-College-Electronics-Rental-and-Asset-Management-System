import psycopg2

conn = psycopg2.connect(dbname='campus_rental', user='postgres', password='postgres', host='localhost', port=5432)
cur = conn.cursor()

# Check existing columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='devices' ORDER BY ordinal_position;")
print('DEVICES:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='return_inspections' ORDER BY ordinal_position;")
print('RETURN_INSPECTIONS:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='rentals' ORDER BY ordinal_position;")
print('RENTALS:', [r[0] for r in cur.fetchall()])

# Run migrations
cur.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS deposit_amount FLOAT NOT NULL DEFAULT 0.0;")
cur.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS is_non_electronic BOOLEAN NOT NULL DEFAULT FALSE;")
cur.execute("ALTER TABLE return_inspections ADD COLUMN IF NOT EXISTS damage_description TEXT;")
conn.commit()
print("Migration done!")
cur.close()
conn.close()
