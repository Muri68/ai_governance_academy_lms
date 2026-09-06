import re
from django import template

register = template.Library()

@register.filter
def youtube_embed(url):
    """Convert YouTube watch URL to embed URL"""
    if not url:
        return ''
    
    # Already an embed URL
    if 'youtube.com/embed/' in url:
        return url
    
    # youtube.com/watch?v=VIDEO_ID
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    
    # youtu.be/VIDEO_ID
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    
    # vimeo.com/12345
    match = re.search(r'vimeo\.com/(\d+)', url)
    if match:
        return f'https://player.vimeo.com/video/{match.group(1)}'
    
    return url