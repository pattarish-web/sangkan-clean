import json
import os
from pathlib import Path
from generate_blog import _fallback_image_url

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "posts.json"

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment.")
        return 1
        
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        posts = json.load(f)
        
    if len(posts) < 6:
        print("Not enough posts to update.")
        return 0
        
    print(f"Updating the last 6 posts in posts.json using OpenAI Multimodal selection...")
    for i in range(-6, 0):
        post = posts[i]
        title = post.get("title")
        category = post.get("category")
        
        # Determine a keyword from title or default category keywords
        keyword = title
        print(f"Post {i}: '{title}' [{category}]")
        
        # Get the new fallback image url using OpenAI Multimodal
        new_url = _fallback_image_url(keyword, category, title)
        print(f"  Old URL: {post.get('image')}")
        print(f"  New URL: {new_url}")
        post["image"] = new_url
        
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        
    print("Done updating posts.json.")
    
    # Rebuild the site files (HTML and listings) to reflect the new images
    try:
        import build_blogs
        import build_listings
        import update_sitemap
        build_blogs.build_blogs()
        build_listings.build_listings()
        update_sitemap.update_sitemap()
        print("Rebuild of site files successful.")
    except Exception as exc:
        print(f"Error rebuilding site files: {exc}")
        return 1
        
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
