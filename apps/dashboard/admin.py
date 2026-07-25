from django.contrib import admin
from .models import SiteSetting, SiteFileSetting

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'setting_type', 'updated_at']
    list_filter = ['setting_type']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['updated_at']
    
    def value_preview(self, obj):
        if obj.value:
            return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
        return '-'
    value_preview.short_description = 'Value'

@admin.register(SiteFileSetting)
class SiteFileSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'file_preview', 'file_name', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at', 'file_preview']
    
    def file_preview(self, obj):
        if obj.file:
            return f'<img src="{obj.file.url}" style="max-height:40px;" />'
        return '-'
    file_preview.allow_tags = True
    file_preview.short_description = 'Preview'
    
    def file_name(self, obj):
        return obj.file_name()
    file_name.short_description = 'File Name'