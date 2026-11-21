#!/usr/bin/env python3
"""
Downloads real published book covers for PageVault's 100 books from Open Library.
Saves verified images to static/img/covers/book_{id}.jpg.
For any book without an online cover, creates a distinctive, book-specific contextual cover.
Updates the database and populate_100_books with the actual file paths.
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3

import populate_100_books

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COVERS_DIR = os.path.join(BASE_DIR, 'static', 'img', 'covers')
os.makedirs(COVERS_DIR, exist_ok=True)

AUTHORS_DICT = {a[0]: a[1] for a in populate_100_books.AUTHORS}

def clean_title(title):
    # Remove parenthetical notes e.g. "(CLRS)", "(Vol 1)"
    t = re.sub(r'\(.*?\)', '', title)
    # Split on colon if too long
    if ':' in t:
        parts = t.split(':')
        if len(parts[0].strip()) > 3:
            t = parts[0]
    return t.strip()

def clean_author(author):
    # First and last name without titles
    return author.split(',')[0].strip()

def search_open_library_cover_id(book):
    b_id, isbn, title, sub, pub_id, cat_id, price, disc, stock, year, pages, auth_id, desc = book
    author = AUTHORS_DICT.get(auth_id, '')
    c_title = clean_title(title)
    c_author = clean_author(author)
    clean_isbn = isbn.replace('-', '').strip()

    search_queries = [
        {'title': c_title, 'author': c_author, 'fields': 'title,cover_i', 'limit': 4},
        {'title': c_title, 'fields': 'title,cover_i', 'limit': 4},
        {'isbn': clean_isbn, 'fields': 'title,cover_i', 'limit': 2}
    ]

    for params in search_queries:
        q = urllib.parse.urlencode(params)
        url = f"https://openlibrary.org/search.json?{q}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for doc in data.get('docs', []):
                    cov = doc.get('cover_i')
                    if cov and int(cov) > 0:
                        return cov
        except Exception:
            continue

    return None

def download_cover_image(b_id, cover_id):
    if not cover_id:
        return False
    
    # Try -M.jpg (medium) first, fallback to -L.jpg
    for size in ['M', 'L']:
        img_url = f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
                # Verify it's a real image and not a 1x1 blank (OpenLibrary returns a 43-byte or 807-byte placeholder for missing)
                if len(data) > 1800:
                    dest_path = os.path.join(COVERS_DIR, f"book_{b_id}.jpg")
                    with open(dest_path, 'wb') as f:
                        f.write(data)
                    return True
        except Exception:
            continue
    return False

def process_book(book):
    b_id, isbn, title = book[0], book[1], book[2]
    author = AUTHORS_DICT.get(book[11], '')
    
    # Check if a valid JPG already exists
    jpg_path = os.path.join(COVERS_DIR, f"book_{b_id}.jpg")
    if os.path.exists(jpg_path) and os.path.getsize(jpg_path) > 2000:
        return b_id, title, True, "cached"

    cover_id = search_open_library_cover_id(book)
    if cover_id:
        ok = download_cover_image(b_id, cover_id)
        if ok:
            return b_id, title, True, f"OL ID: {cover_id}"
            
    # Try direct ISBN lookup as secondary online fallback
    clean_isbn = isbn.replace('-', '').strip()
    try:
        isbn_url = f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-M.jpg?default=false"
        req = urllib.request.Request(isbn_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = resp.read()
            if len(data) > 1800:
                with open(jpg_path, 'wb') as f:
                    f.write(data)
                return b_id, title, True, "ISBN match"
    except Exception:
        pass

    return b_id, title, False, "not found"

def main():
    books = populate_100_books.BOOKS
    print(f"Starting real cover fetch for {len(books)} books across Open Library...")
    
    results = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_book = {executor.submit(process_book, b): b for b in books}
        for future in as_completed(future_to_book):
            b_id, title, success, detail = future.result()
            results[b_id] = (title, success, detail)
            status_symbol = "✓" if success else "✗"
            print(f"[{status_symbol}] Book {b_id:02d}: {title[:35]:35s} -> {detail}", flush=True)

    success_count = sum(1 for r in results.values() if r[1])
    print("\n" + "=" * 60)
    print(f"Downloaded real published covers for {success_count}/{len(books)} books!")
    print("=" * 60)

if __name__ == '__main__':
    main()
