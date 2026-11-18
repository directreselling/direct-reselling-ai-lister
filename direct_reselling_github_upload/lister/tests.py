from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Batch, Item
from .services import make_title

class ListerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="test-pass-123")
        self.batch = Batch.objects.create(owner=self.user, name="Test")
        self.item = Item.objects.create(batch=self.batch, sku="DR-TEST", brand="Levis",
                                        item_type="Jeans", gender="Mens", size="Large",
                                        colour="Blue", keywords="Straight Leg")
    def test_login_required(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)
    def test_owner_can_see_batch(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("batch", args=[self.batch.pk])).status_code, 200)
    def test_title_order(self):
        self.assertEqual(make_title(self.item), "Levis Jeans Mens Large Blue Straight Leg")
    def test_title_limit(self):
        self.item.keywords = "A" * 100
        self.assertLessEqual(len(make_title(self.item)), 80)
    def test_cannot_approve_without_price(self):
        self.client.force_login(self.user)
        self.client.post(reverse("approve", args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "draft")

    def test_invalid_upload_creates_no_batch(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.user)
        before = Batch.objects.count()
        response = self.client.post(reverse("upload"), {"name": "Invalid", "photos": [
            SimpleUploadedFile("bad.jpg", b"not a photo", content_type="image/jpeg")
        ]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Batch.objects.count(), before)

    def test_photo_limit_on_move(self):
        from django.core.files.base import ContentFile
        from .models import Photo
        self.client.force_login(self.user)
        target = Item.objects.create(batch=self.batch, sku="DR-TARGET")
        source = Item.objects.create(batch=self.batch, sku="DR-SOURCE")
        for i in range(15):
            Photo.objects.create(item=target, image=ContentFile(b"a", name=f"target{i}.jpg"), original_name=f"target{i}.jpg")
        photo = Photo.objects.create(item=source, image=ContentFile(b"b", name="source.jpg"), original_name="source.jpg")
        self.client.post(reverse("move_photo", args=[photo.pk]), {"target": target.pk})
        photo.refresh_from_db()
        self.assertEqual(photo.item_id, source.pk)

from unittest.mock import patch
from .ai_service import AIListingError

class AIWorkflowTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user(username='aiuser', password='test-pass-123')
        self.batch = Batch.objects.create(owner=self.user, name='AI test')
        self.item = Item.objects.create(batch=self.batch, sku='AI-TEST', brand='User brand')
        self.client.force_login(self.user)

    def test_rejects_no_photos(self):
        response = self.client.post(f'/item/{self.item.pk}/ai-generate/', {'photos': []})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.get(pk=self.item.pk).title, '')

    @patch('lister.views.generate', side_effect=AIListingError('Unavailable'))
    def test_failed_generation_keeps_item_unchanged(self, mock_generate):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image
        output = BytesIO(); Image.new('RGB',(10,10)).save(output,'JPEG')
        photo = Photo.objects.create(item=self.item,image=SimpleUploadedFile('x.jpg',output.getvalue(),content_type='image/jpeg'),original_name='x.jpg')
        response = self.client.post(f'/item/{self.item.pk}/ai-generate/', {'photos':[str(photo.pk)]})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Item.objects.get(pk=self.item.pk).title,'')
