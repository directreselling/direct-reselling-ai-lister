from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Batch', fields=[('id', models.BigAutoField(primary_key=True, serialize=False)),('name',models.CharField(max_length=150)),('created_at',models.DateTimeField(auto_now_add=True)),('owner',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to=settings.AUTH_USER_MODEL))]),
        migrations.CreateModel(name='Item', fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('sku',models.CharField(max_length=30,unique=True)),('title',models.CharField(max_length=80,blank=True)),('brand',models.CharField(max_length=100,blank=True)),('item_type',models.CharField(max_length=100,blank=True)),('gender',models.CharField(max_length=30,blank=True)),('size',models.CharField(max_length=50,blank=True)),('colour',models.CharField(max_length=50,blank=True)),('keywords',models.CharField(max_length=200,blank=True)),('description',models.TextField(blank=True)),('condition_notes',models.TextField(blank=True)),('price',models.DecimalField(max_digits=9,decimal_places=2,null=True,blank=True)),('purchase_cost',models.DecimalField(max_digits=9,decimal_places=2,null=True,blank=True)),('storage_location',models.CharField(max_length=100,blank=True)),('status',models.CharField(choices=[('draft','Draft'),('approved','Approved'),('published','Published')],default='draft',max_length=12)),('ebay_listing_id',models.CharField(max_length=100,blank=True)),('created_at',models.DateTimeField(auto_now_add=True)),('batch',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='items',to='lister.batch'))]),
        migrations.CreateModel(name='Photo', fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('image',models.ImageField(upload_to='items/%Y/%m/')),('original_name',models.CharField(max_length=255)),('created_at',models.DateTimeField(auto_now_add=True)),('item',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='photos',to='lister.item'))]),
        migrations.AddField(model_name='item',name='ai_aspects',field=models.JSONField(blank=True,default=dict)),
        migrations.AddField(model_name='item',name='ai_evidence',field=models.JSONField(blank=True,default=dict)),
    ]
