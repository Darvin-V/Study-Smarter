from src.database.connection import get_db_cursor

with get_db_cursor() as cur:
    cur.execute("""
        SELECT COUNT(*) as count FROM questions 
        WHERE explanation LIKE '%Low Confidence%' 
           OR explanation LIKE '%Unable to determine%' 
           OR explanation LIKE '%held for review%' 
           OR explanation LIKE '%NEEDS_REVIEW%'
    """)
    bad = cur.fetchone()["count"]
    
    cur.execute("SELECT COUNT(*) as count FROM questions WHERE verification_status = 'AI_VERIFIED'")
    ai_verified = cur.fetchone()["count"]
    
    cur.execute("SELECT COUNT(*) as count FROM questions WHERE verification_status = 'NEEDS_REVIEW'")
    needs_review = cur.fetchone()["count"]
    
    cur.execute("SELECT COUNT(*) as count FROM questions")
    total = cur.fetchone()["count"]
    
    print(f"Total: {total}, Bad explanations: {bad}, AI_VERIFIED: {ai_verified}, NEEDS_REVIEW: {needs_review}")
