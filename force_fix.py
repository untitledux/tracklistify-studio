import sqlite3
import os

DB_PATH = 'tracklistify.db'

def fix():
    if not os.path.exists(DB_PATH):
        print(f'Database {DB_PATH} not found.')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print('--- Patching Database Columns ---')

    # 1. Add dj_id to tracks
    try:
        print('Attempting to add dj_id to tracks...')
        cur.execute('ALTER TABLE tracks ADD COLUMN dj_id INTEGER REFERENCES djs(id)')
        print(' [SUCCESS] Added dj_id')
    except sqlite3.OperationalError as e:
        print(f' [INFO] dj_id exists or error: {e}')

    # 2. Add label_id to tracks (just in case)
    try:
        print('Attempting to add label_id to tracks...')
        cur.execute('ALTER TABLE tracks ADD COLUMN label_id INTEGER REFERENCES labels(id)')
        print(' [SUCCESS] Added label_id')
    except sqlite3.OperationalError as e:
        print(f' [INFO] label_id exists or error: {e}')

    conn.commit()
    conn.close()
    print('--- Database Patch Complete ---')

if __name__ == '__main__':
    fix()


