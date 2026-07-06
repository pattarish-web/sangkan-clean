import os

def fix_line_id(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Revert to @sangkanclean
    content = content.replace('line.me/ti/p/@sankanclean', 'line.me/ti/p/@sangkanclean')
    content = content.replace('line.me/R/ti/p/@sankanclean', 'line.me/R/ti/p/@sangkanclean')
    
    # Use standard capitalization for display if you want, or lowercase. The user explicitly typed @sangkanclean
    content = content.replace('@sankanclean', '@sangkanclean')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for filename in os.listdir('.'):
    if filename.endswith('.html') or filename.endswith('.js'):
        fix_line_id(filename)

print("Fixed Line IDs back to @sangkanclean.")
