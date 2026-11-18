from django.conf import settings
from django.db import models

class Batch(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Item(models.Model):
    STATUS = [("draft", "Draft"), ("approved", "Approved"), ("published", "Published")]
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="items")
    sku = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=80, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    item_type = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    size = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=50, blank=True)
    keywords = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    condition_notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    storage_location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="draft")
    ai_aspects = models.JSONField(default=dict, blank=True)
    ai_evidence = models.JSONField(default=dict, blank=True)
    ebay_listing_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.sku

class Photo(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="items/%Y/%m/")
    original_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
