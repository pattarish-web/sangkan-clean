import os
import json
import re

def update_domain():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    domain = config.get('domain', '').rstrip('/')
    if not domain:
        print("Error: No domain found in config.json")
        return

    # Update HTML files
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Update og:url
        # <meta property="og:url" content="...">
        content = re.sub(
            r'(<meta property="og:url" content=")([^"]+)(">)', 
            rf'\g<1>{domain}/{html_file if html_file != "index.html" else ""}\g<3>', 
            content
        )
        
        # Update canonical
        # <link rel="canonical" href="...">
        content = re.sub(
            r'(<link rel="canonical" href=")([^"]+)(">)', 
            rf'\g<1>{domain}/{html_file if html_file != "index.html" else ""}\g<3>', 
            content
        )
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

    # Update sitemap.xml
    if os.path.exists('sitemap.xml'):
        with open('sitemap.xml', 'r', encoding='utf-8') as f:
            sitemap_content = f.read()
            
        # Update <loc>https://old-domain/path</loc> -> <loc>https://new-domain/path</loc>
        def sitemap_repl(m):
            basename = m.group(1).strip('/').split('/')[-1]
            if basename.endswith('.html'):
                return f'<loc>{domain}/{basename}</loc>'
            else:
                return f'<loc>{domain}/</loc>'
            
        sitemap_content = re.sub(
            r'<loc>(.*?)</loc>', 
            sitemap_repl, 
            sitemap_content
        )
        
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
            
    # Update robots.txt
    if os.path.exists('robots.txt'):
        with open('robots.txt', 'r', encoding='utf-8') as f:
            robots_content = f.read()
            
        robots_content = re.sub(
            r'Sitemap: https?://[^\s]+/sitemap.xml',
            f'Sitemap: {domain}/sitemap.xml',
            robots_content
        )
        
        with open('robots.txt', 'w', encoding='utf-8') as f:
            f.write(robots_content)
            
    print(f"Domain successfully updated to: {domain} across all files!")

if __name__ == '__main__':
    update_domain()
