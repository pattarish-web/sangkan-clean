import re

def update_blog_html():
    with open('blog.html', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace the renderGrid function
    old_render_grid = """        function renderGrid(posts) {
            if (posts.length === 0) {
                blogGrid.innerHTML = '<div class="no-posts">ยังไม่มีบทความในขณะนี้ครับ</div>';
                return;
            }
            blogGrid.innerHTML = posts.map((post, index) => `
                <div class="blog-card" onclick="openModal(${allPosts.indexOf(post)})">
                    <img src="${post.image}" alt="${post.title}" class="blog-card-img">
                    <div class="blog-card-body">
                        <span class="blog-card-tag">${post.category}</span>
                        <h2 class="blog-card-title">${post.title}</h2>
                        <p class="blog-card-desc">${post.description}</p>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="blog-card-date"><i class="fa-regular fa-calendar"></i> ${post.date}</span>
                            <span class="blog-card-read">อ่านต่อ <i class="fa-solid fa-arrow-right"></i></span>
                        </div>
                    </div>
                </div>
            `).join('');
        }"""
        
    new_render_grid = """        function renderGrid(posts) {
            if (posts.length === 0) {
                blogGrid.innerHTML = '<div class="no-posts">ยังไม่มีบทความในขณะนี้ครับ</div>';
                return;
            }
            blogGrid.innerHTML = posts.map((post) => {
                const slug = post.slug || 'post';
                return `
                <a href="blog/${slug}.html" class="blog-card" style="text-decoration:none;">
                    <img src="${post.image}" alt="${post.title}" class="blog-card-img">
                    <div class="blog-card-body">
                        <span class="blog-card-tag">${post.category}</span>
                        <h2 class="blog-card-title">${post.title}</h2>
                        <p class="blog-card-desc">${post.description}</p>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="blog-card-date"><i class="fa-regular fa-calendar"></i> ${post.date}</span>
                            <span class="blog-card-read">อ่านต่อ <i class="fa-solid fa-arrow-right"></i></span>
                        </div>
                    </div>
                </a>
                `;
            }).join('');
        }"""
        
    content = content.replace(old_render_grid, new_render_grid)
    
    with open('blog.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Updated blog.html")

if __name__ == '__main__':
    update_blog_html()
