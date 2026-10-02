from src.database.connection import get_db_cursor

with get_db_cursor() as cur:
    cur.execute("SELECT COUNT(*) as c FROM questions;")
    total = cur.fetchone()['c']
    cur.execute("""SELECT COUNT(*) as c FROM questions WHERE explanation LIKE '%Low Confidence%' 
           OR explanation LIKE '%Unable to determine%' 
           OR explanation LIKE '%held for review%' 
           OR explanation LIKE '%AI verified%' 
           OR explanation LIKE '%Unverified%'
           OR explanation LIKE '%Flagged for review%';""")
    bad = cur.fetchone()['c']
    print(f"Total questions: {total}, Bad explanation rows: {bad}")
