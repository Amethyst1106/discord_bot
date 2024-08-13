import os
import psycopg2
from psycopg2.extras import DictCursor

db_url = os.getenv("DB_URL")

def select(sql):
    con = psycopg2.connect(db_url)
    cur = con.cursor(cursor_factory=DictCursor)
    cur.execute(sql)
    data = cur.fetchall()
    cur.close()
    con.close()
    return data

def insert(table, dic):
    columns = list()
    values = list()
    for key in dic:
        columns.append(key)
        values.append(dic[key])
    sql = f'\
            INSERT INTO \
                {table} \
            ({", ".join(columns)}) \
            VALUES \
            ({",".join(["%s"]*len(columns))})\
            '
    con = psycopg2.connect(db_url)
    cur = con.cursor()
    cur.execute(sql, tuple(values))
    con.commit()
    cur.close()
    con.close()