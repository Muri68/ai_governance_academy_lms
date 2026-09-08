from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Post, Category, Tag, Comment


def blog_home(request):
    """Blog homepage with featured and recent posts"""
    featured_posts = Post.objects.filter(
        status='published',
        is_featured=True,
        published_at__isnull=False,
        published_at__lte=timezone.now()
    ).select_related('author', 'category')[:5]
    
    recent_posts = Post.objects.filter(
        status='published',
        published_at__isnull=False,
        published_at__lte=timezone.now()
    ).select_related('author', 'category').prefetch_related('tags')[:6]
    
    categories = Category.objects.filter(
        is_active=True,
        posts__status='published'
    ).annotate(post_count=Count('posts')).order_by('-post_count')[:10]
    
    tags = Tag.objects.filter(
        posts__status='published'
    ).annotate(post_count=Count('posts')).order_by('-post_count')[:20]
    
    context = {
        'featured_posts': featured_posts,
        'recent_posts': recent_posts,
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'blog/home.html', context)


def post_detail(request, slug):
    """Single blog post view"""
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'related_course').prefetch_related('tags'),
        slug=slug,
        status='published',
        published_at__isnull=False,
        published_at__lte=timezone.now()
    )
    
    post.increment_views()
    
    comments = post.comments.filter(
        is_approved=True,
        parent=None
    ).select_related('author').prefetch_related('replies')
    
    related_posts = post.related_posts
    
    categories = Category.objects.filter(
        is_active=True,
        posts__status='published'
    ).annotate(post_count=Count('posts'))[:10]
    
    tags = Tag.objects.filter(
        posts__status='published'
    ).annotate(post_count=Count('posts'))[:20]
    
    context = {
        'post': post,
        'comments': comments,
        'related_posts': related_posts,
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'blog/post_detail.html', context)


def category_detail(request, slug):
    """Posts by category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    posts_list = Post.objects.filter(
        category=category,
        status='published',
        published_at__isnull=False,
        published_at__lte=timezone.now()
    ).select_related('author').prefetch_related('tags')
    
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': posts,
    }
    return render(request, 'blog/category_detail.html', context)


def tag_detail(request, slug):
    """Posts by tag"""
    tag = get_object_or_404(Tag, slug=slug)
    
    posts_list = Post.objects.filter(
        tags=tag,
        status='published',
        published_at__isnull=False,
        published_at__lte=timezone.now()
    ).select_related('author', 'category').prefetch_related('tags')
    
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'posts': posts,
    }
    return render(request, 'blog/tag_detail.html', context)


def blog_search(request):
    """Search blog posts"""
    query = request.GET.get('q', '')
    
    if query:
        posts_list = Post.objects.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query),
            status='published',
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags')
    else:
        posts_list = Post.objects.none()
    
    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'posts': posts,
        'query': query,
    }
    return render(request, 'blog/search_results.html', context)


@login_required
def add_comment(request, slug):
    """Add comment to a post"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                is_approved=True
            )
            messages.success(request, 'Your comment has been added successfully.')
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    return redirect('blog:post_detail', slug=slug)


@login_required
def add_reply(request, slug, comment_id):
    """Add reply to a comment"""
    post = get_object_or_404(Post, slug=slug, status='published')
    parent_comment = get_object_or_404(Comment, id=comment_id, post=post)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                parent=parent_comment,
                content=content,
                is_approved=True
            )
            messages.success(request, 'Your reply has been added successfully.')
        else:
            messages.error(request, 'Reply cannot be empty.')
    
    return redirect('blog:post_detail', slug=slug)