import sqlite3
import os.path as path


# TODO: assumes db is called 'db.sqlite'
db_name = 'db.sqlite'


def get_db(repository):
    return path.join(repository, db_name)


def get_connection(repository):
    db_file = get_db(repository)
    return sqlite3.connect(db_file)


def init(repository):
    "Init an empty database if doesn't exist."
    db_file = get_db(repository)
    if not path.exists(db_file):
        con = sqlite3.connect(db_file)
        c = con.cursor()
        c.execute("""
        CREATE TABLE file (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        hash CHAR(40))""")

        c.execute("CREATE INDEX ix_hash ON file(hash)")

        c.execute("""
        CREATE TABLE tag (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255))""")

        c.execute("""
        CREATE TABLE file_tag (
        file_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (file_id, tag_id))""")

        con.commit()
        con.close()


def tag_exists(con, tag):
    c = con.cursor()
    c.execute("SELECT id FROM tag WHERE name = ?", (tag,))
    return c.fetchone() is not None


def tag_add(con, tag):
    c = con.cursor()
    c.execute("INSERT INTO tag (name) VALUES (?)", (tag,))
    con.commit()


def tag_get_id(con, tag):
    c = con.cursor()
    c.execute("SELECT id FROM tag WHERE name = ?", (tag,))
    return c.fetchone()[0]


def file_exists(con, file_hash):
    c = con.cursor()
    c.execute("SELECT id FROM file WHERE hash = ?", (file_hash,))
    return c.fetchone() is not None


def file_tagged(con, file_hash, tag):
    c = con.cursor()
    c.execute("""
    SELECT * FROM file f
    JOIN file_tag ft ON (f.id = ft.file_id)
    JOIN tag t ON (ft.tag_id = t.id)
    WHERE f.hash = ? AND t.name = ?
    """, (file_hash, tag))
    return c.fetchone() is not None


def file_add(con, file_name, file_hash):
    c = con.cursor()
    c.execute("INSERT INTO file (name, hash) VALUES (?, ?)",
              (file_name, file_hash))
    con.commit()


def file_get_id(con, file_hash):
    c = con.cursor()
    c.execute("SELECT id FROM file WHERE hash = ?", (file_hash,))
    return c.fetchone()[0]


# TODO: consider multiple files can have same name, what should we do
# then?
def file_get_hash(con, file_name):
    c = con.cursor()
    c.execute("SELECT hash FROM file WHERE name = ?", (file_name,))
    re = c.fetchone()
    if re is not None:
        return re[0]
    else:
        return re


def file_tag(repository, file_name, file_hash, tag):
    "Add tag to a file."
    with get_connection(repository) as con:
        # check if file exists, if not, add it
        if not file_exists(con, file_hash):
            file_add(con, file_name, file_hash)

        # check if tag exists, if not, add it
        if not tag_exists(con, tag):
            tag_add(con, tag)

        # check if file is already tagged with this file, if not, tag it
        if not file_tagged(con, file_hash, tag):
            c = con.cursor()
            tag_id = tag_get_id(con, tag)
            file_id = file_get_id(con, file_hash)
            print((file_id, tag_id))
            c.execute("INSERT INTO file_tag VALUES (?, ?)", (file_id, tag_id))


def get_tagged_files(repository, tags):
    "Get all files in repository tagged with tags."
    if not tags:
        return []

    with get_connection(repository) as con:
        c = con.cursor()
        q = """
        SELECT f.name, f.hash FROM file f
        JOIN file_tag ft ON (f.id = ft.file_id)
        JOIN tag t ON (ft.tag_id = t.id)
        WHERE t.name IN ({0})
        GROUP BY f.name, f.hash
        HAVING count(distinct t.id) = {1}
        """.format(','.join(['?'] * len(tags)), len(tags))
        c.execute(q, tuple(tags))
        return c.fetchall()
