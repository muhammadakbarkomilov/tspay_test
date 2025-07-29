from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import models
from .models import BlogPost, Tag


def blog_list(request):
    # Filter by tag if specified
    tag_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')

    posts = BlogPost.objects.all().order_by('-created_at')

    if tag_filter != 'all':
        posts = posts.filter(tags__name=tag_filter)

    if search_query:
        posts = posts.filter(
            models.Q(title__icontains=search_query) |
            models.Q(content__icontains=search_query)
        )

    # Get popular tags (tags with most posts)
    popular_tags = Tag.objects.annotate(num_posts=Count('blogpost')).order_by('-num_posts')[:10]
    all_tags = Tag.objects.annotate(num_posts=Count('blogpost')).order_by('name')

    # Get popular posts (most viewed)
    popular_posts = BlogPost.objects.all().order_by('-views')[:5]

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'posts': page_obj,
        'popular_tags': popular_tags,
        'all_tags': all_tags,
        'popular_posts': popular_posts,
    }
    return render(request, 'blog/index.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)

    # Get related posts (posts with same tags)
    related_posts = BlogPost.objects.filter(
        tags__in=post.tags.all()
    ).exclude(id=post.id).distinct().order_by('-created_at')[:4]

    # Get popular posts (most viewed)
    popular_posts = BlogPost.objects.all().exclude(id=post.id).order_by('-views')[:5]

    context = {
        'post': post,
        'related_posts': related_posts,
        'popular_posts': popular_posts,
    }
    return render(request, 'blog/detail.html', context)


@require_POST
def increment_view(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, id=post_id)
        post.views += 1
        post.save()
        return JsonResponse({'status': 'success', 'views': post.views})
    return JsonResponse({'status': 'error'}, status=400)


@require_POST
def increment_click(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, id=post_id)
        post.clicks += 1
        post.save()
        return JsonResponse({'status': 'success', 'clicks': post.clicks})
    return JsonResponse({'status': 'error'}, status=400)