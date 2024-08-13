import os
import psycopg2
from psycopg2.extras import DictCursor

db_url = os.getenv("DB_URL")

def select(sql):
    data = []
    with psycopg2.connect(db_url) as con:
        with con.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql)
            data = cur.fetchall()
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
    with psycopg2.connect(db_url) as con:
        with con.cursor() as cur:
            cur.execute(sql, tuple(values))
            con.commit()