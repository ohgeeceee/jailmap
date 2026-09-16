import traceback, os, psycopg
from backend.adapters import carter_json
with psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row) as c:
    src = c.execute("select * from records.jurisdictions where state=%s and county=%s", ("MT","Carter")).fetchone()
try:
    rows = carter_json.fetch(src)
    print("OK, got", len(rows), "rows")
    if rows:
        print("row keys:", sorted(rows[0].keys()))
        print("sample:", {k: rows[0][k] for k in rows[0] if k != "charges"})
        print("charge sample:", rows[0]["charges"][:1])
except Exception:
    traceback.print_exc()
