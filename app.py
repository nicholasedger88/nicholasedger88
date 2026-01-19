from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "books.db"


def create_app() -> Flask:
    app = Flask(__name__)
    init_db()

    @app.get("/")
    def index() -> str:
        books = fetch_books()
        stats = summarize_books(books)
        return render_template("index.html", books=books, stats=stats)

    @app.route("/add", methods=["GET", "POST"])
    def add_book() -> str:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            notes = request.form.get("notes", "").strip()
            if title:
                insert_book(title=title, author=author, notes=notes)
                return redirect(url_for("index"))
            return render_template(
                "add.html",
                error="Please provide a title.",
                form_data={"title": title, "author": author, "notes": notes},
            )
        return render_template("add.html", error=None, form_data=None)

    @app.post("/toggle/<int:book_id>")
    def toggle_book(book_id: int) -> str:
        toggle_read(book_id)
        return redirect(url_for("index"))

    @app.post("/delete/<int:book_id>")
    def delete_book(book_id: int) -> str:
        remove_book(book_id)
        return redirect(url_for("index"))

    return app


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                notes TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def fetch_books() -> list[dict[str, str | int]]:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, title, author, notes, is_read, created_at FROM books ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def insert_book(*, title: str, author: str, notes: str) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT INTO books (title, author, notes) VALUES (?, ?, ?)",
            (title, author or None, notes or None),
        )
        connection.commit()


def toggle_read(book_id: int) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "UPDATE books SET is_read = CASE WHEN is_read = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (book_id,),
        )
        connection.commit()


def remove_book(book_id: int) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        connection.commit()


def summarize_books(books: list[dict[str, str | int]]) -> dict[str, int]:
    total = len(books)
    read = sum(1 for book in books if book["is_read"])
    return {"total": total, "read": read, "unread": total - read}


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
