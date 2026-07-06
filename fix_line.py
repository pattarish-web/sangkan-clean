import os
import re

def fix_line_id(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the URLs
    content = content.replace('line.me/ti/p/@sangkanclean', 'line.me/ti/p/@sankanclean')
    content = content.replace('line.me/R/ti/p/@sangkanclean', 'line.me/R/ti/p/@sankanclean')
    
    # Fix the display text
    content = content.replace('@SangkanClean', '@sankanclean')
    content = content.replace('@sangkanclean', '@sankanclean')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for filename in os.listdir('.'):
    if filename.endswith('.html') or filename.endswith('.js'):
        fix_line_id(filename)

print("Fixed Line IDs.")
