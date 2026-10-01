#!/usr/bin/env python3
"""
Adds a matching trucking photo to articles and guides that don't have one yet.
Runs with every site update (.github/workflows/update.yml), up to 8 photos per run.
Needs the PIXABAY_API_KEY secret (free key at pixabay.com/api/docs). Skips quietly if missing.
"""
import os
import write_article

if __name__ == "__main__":
    if not (os.environ.get("PIXABAY_API_KEY", "").strip() or os.environ.get("PEXELS_API_KEY", "").strip()):
        print("No PIXABAY_API_KEY secret set; articles keep their topic card images.")
    else:
        write_article.backfill_photos(limit=8)
