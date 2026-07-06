import os
import json
import re

def fix_posts_json():
    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)

    for post in posts:
        # Fix description
        post['description'] = post['description'].replace('บริการ บริการ', 'บริการ')
        post['description'] = post['description'].replace('บริการบริการ', 'บริการ')
        
        # Fix title
        post['title'] = post['title'].replace('บริการ บริการ', 'บริการ')
        post['title'] = post['title'].replace('บริการบริการ', 'บริการ')
        
        # Fix content
        post['content'] = post['content'].replace('บริการ บริการ', 'บริการ')
        post['content'] = post['content'].replace('บริการบริการ', 'บริการ')

    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

def fix_post_files():
    if not os.path.exists('posts'):
        return
        
    for filename in os.listdir('posts'):
        if not filename.endswith('.md'):
            continue
            
        filepath = os.path.join('posts', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace('บริการ บริการ', 'บริการ')
        content = content.replace('บริการบริการ', 'บริการ')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    fix_posts_json()
    fix_post_files()
    print("Fixed redundant words in posts")
