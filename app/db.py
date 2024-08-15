import os
import psycopg2
from psycopg2.extras import DictCursor

db_url = os.getenv("DB_URL")

def select_all(table):
    data = []
    with psycopg2.connect(db_url) as con:
        with con.cursor(cursor_factory=DictCursor) as cur:
            sql = f"SELECT * FROM {table}"
            cur.execute(sql)
            data = cur.fetchall()
    return data

def insert_dic(table, dic):
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

def delete_by_rule(table, rule):
    with psycopg2.connect(db_url) as con:
        with con.cursor() as cur:
            sql = f"DELETE FROM {table} WHERE {rule}"
            cur.execute(sql)
            con.commit()