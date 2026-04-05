from django.contrib import admin
from .models import Advertisement, Category, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'price', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'is_featured']
    search_fields = ['title', 'description', 'user__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'user')
        }),
        ('Pricing & Category', {
            'fields': ('price', 'category', 'city')
        }),
        ('Status & Features', {
            'fields': ('status', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('views', 'created_at', 'updated_at')
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['ad', 'user', 'text_preview', 'is_reply', 'created_at']
    list_filter = ['created_at', 'parent']
    search_fields = ['user__username', 'ad__title', 'text']
    readonly_fields = ['created_at']
    raw_id_fields = ['ad', 'user', 'parent']

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'

    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Is Reply'
