import json
import os
import re

def slugify(text):
    # Convert spaces to hyphens and remove any chars that are not alphanumeric or Thai
    text = re.sub(r'\s+', '-', text.strip())
    # Allow a-z, A-Z, 0-9, and Thai unicode range
    text = re.sub(r'[^\w\u0E00-\u0E7F\-]', '', text)
    return text.lower()

def build_blogs():
    if not os.path.exists('blog'):
        os.makedirs('blog')
        
    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
        
    with open('blog_template.html', 'r', encoding='utf-8') as f:
        template = f.read()
        
    # Update posts with slugs so blog.html can read it
    updated_posts = []
    
    for i, post in enumerate(posts):
        # Generate slug from title
        slug = slugify(post['title'])
        if not slug:
            slug = f"post-{i}"
            
        post['slug'] = slug
        
        # Build HTML content
        content = post.get('content', '')
        if not content:
            content = f"""<p>{post['description']}</p>
                   <p>บทความนี้กำลังอยู่ในระหว่างการจัดทำเนื้อหาเพิ่มเติม โปรดติดตามอัปเดตจากเราได้เร็วๆ นี้ครับ</p>
                   <p>สนใจสอบถามบริการทำความสะอาดเพิ่มเติม ติดต่อทีมงาน Sangkan Clean ได้เลยครับ</p>"""
                   
        html = template.replace('{{title}}', post['title'])
        html = html.replace('{{description}}', post['description'])
        html = html.replace('{{image}}', post['image'])
        html = html.replace('{{category}}', post['category'])
        html = html.replace('{{date}}', post['date'])
        html = html.replace('{{slug}}', slug)
        html = html.replace('{{content}}', content)
        
        filepath = os.path.join('blog', f"{slug}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
            
        updated_posts.append(post)
        
    # Save the updated posts.json with slugs so we can link to them
    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(updated_posts, f, ensure_ascii=False, indent=2)
        
    print(f"Generated {len(updated_posts)} static blog posts in blog/ directory.")

if __name__ == '__main__':
    build_blogs()
