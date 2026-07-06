import re
import os

def extract_css(html_file, css_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the <style> block
    style_pattern = re.compile(r'<style>(.*?)</style>', re.DOTALL | re.IGNORECASE)
    match = style_pattern.search(content)

    if match:
        css_content = match.group(1).strip()
        
        # Save to CSS file
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
            
        # Replace <style> block with <link>
        link_tag = f'<link rel="stylesheet" href="{css_file}">'
        new_content = content[:match.start()] + link_tag + content[match.end():]
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"Successfully extracted CSS from {html_file} to {css_file}")
    else:
        print(f"No <style> block found in {html_file}")

if __name__ == '__main__':
    extract_css('landing-bigcleaning.html', 'style-bigcleaning.css')
    extract_css('landing-maid.html', 'style-maid.css')
