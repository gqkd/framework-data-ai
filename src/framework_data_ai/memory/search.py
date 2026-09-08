"""Bounded literal search, with explicit opt-in to an in-memory SQLite FTS5 index.

Neither path emits relations. FTS5 absence degrades to literal text search visibly.
No models, persistent database, downloads or external processes are required.
"""
from __future__ import annotations

from contextlib import closing
import re
import sqlite3


def fts5_available() -> bool:
    try:
        with closing(sqlite3.connect(":memory:")) as database:
            database.execute("CREATE VIRTUAL TABLE probe USING fts5(body)")
        return True
    except sqlite3.Error:
        return False


def search(documents: dict[str, str], text: str, *, engine="literal") -> dict:
    requested = engine
    fallback = None
    terms = [text.casefold()]
    paths = []
    if engine == "fts5":
        tokens = re.findall(r"\w+", text, flags=re.UNICODE)
        terms = [t.casefold() for t in tokens]
        try:
            with closing(sqlite3.connect(":memory:")) as database:
                database.execute("CREATE VIRTUAL TABLE documents USING fts5(path UNINDEXED, body)")
                database.executemany("INSERT INTO documents(path,body) VALUES (?,?)", sorted(documents.items()))
                # Token-only quoted terms: user text cannot inject FTS operators or SQL.
                expression = " OR ".join('"' + token + '"' for token in tokens)
                if expression:
                    paths = [row[0] for row in database.execute(
                        "SELECT path FROM documents WHERE documents MATCH ? ORDER BY bm25(documents), path",
                        (expression,))]
        except sqlite3.Error:
            engine, fallback, terms = "literal", "fts5-unavailable", [text.casefold()]
    if engine == "literal":
        paths = [path for path, body in sorted(documents.items()) if text.casefold() in body.casefold()]
    matches = []
    for path in paths:
        lines = documents[path].splitlines()
        excerpts = [dict(line=i, text=line[:500]) for i, line in enumerate(lines, 1)
                    if any(term and term in line.casefold() for term in terms)][:3]
        matches.append(dict(path=path, excerpts=excerpts))
    return dict(requested_engine=requested, engine=engine, fallback=fallback, matches=matches,
                semantics="retrieval-only; matches are not declared relationships")
