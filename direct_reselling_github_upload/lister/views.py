import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError, ImageOps
from .forms import ItemForm
from .models import Batch, Item, Photo
from .services import make_title
from .ai_service import generate, AIListingError, ASPECTS

@login_required
def dashboard(request):
    batches = Batch.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "lister/dashboard.html", {"batches": batches})

@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk, owner=request.user)
    return render(request, "lister/batch.html", {"batch": batch})

@login_required
@require_POST
def upload(request):
    images = request.FILES.getlist("photos")
    if not images or len(images) > 300:
        return HttpResponseBadRequest("Select 1–300 photos per upload.")
    name = (request.POST.get("name") or "New batch")[:150]
    # Validate the entire batch before writing database rows or media files.
    # A failed upload must not leave half a batch behind.
    for uploaded in images:
        if uploaded.size > 15 * 1024 * 1024:
            return HttpResponseBadRequest("Each image must be 15 MB or smaller.")
        try:
            with Image.open(uploaded) as img:
                if img.format not in ("JPEG", "PNG", "WEBP"):
                    return HttpResponseBadRequest("Only JPEG, PNG and WebP are supported.")
                if img.width * img.height > 50_000_000:
                    return HttpResponseBadRequest("Image dimensions are too large.")
                img.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            return HttpResponseBadRequest("An uploaded file is not a valid image.")
        finally:
            uploaded.seek(0)
    with transaction.atomic():
        batch = Batch.objects.create(owner=request.user, name=name)
        for uploaded in images:
            item = Item.objects.create(batch=batch, sku=f"DR-{uuid.uuid4().hex[:12].upper()}")
            Photo.objects.create(item=item, image=uploaded, original_name=uploaded.name[:255])
    messages.success(request, "Photos uploaded. Group photos belonging to the same item.")
    return redirect("batch", pk=batch.pk)

@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk, batch__owner=request.user)
    form = ItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.ai_aspects = {key: form.cleaned_data["aspect_" + key] for key in ASPECTS}
        item.status = "draft"  # Edits require reapproval.
        item.save()
        messages.success(request, "Draft saved.")
        return redirect("batch", pk=item.batch_id)
    return render(request, "lister/item.html", {"item": item, "form": form, "aspects": item.ai_aspects, "evidence": item.ai_evidence})

@login_required
@require_POST
def title_suggest(request, pk):
    item = get_object_or_404(Item, pk=pk, batch__owner=request.user)
    item.title = make_title(item)
    item.status = "draft"
    item.save(update_fields=["title", "status"])
    return redirect("item", pk=item.pk)

@login_required
@require_POST
def move_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk, item__batch__owner=request.user)
    target = get_object_or_404(Item, pk=request.POST.get("target"), batch=photo.item.batch)
    if target.pk != photo.item_id and target.photos.count() >= 15:
        messages.error(request, "A listing can contain at most 15 photos.")
        return redirect("batch", pk=target.batch_id)
    photo.item = target
    photo.save(update_fields=["item"])
    return redirect("batch", pk=target.batch_id)

@login_required
@require_POST
def approve(request, pk):
    item = get_object_or_404(Item, pk=pk, batch__owner=request.user)
    if not item.title or item.price is None or not item.photos.exists():
        messages.error(request, "A title, price and photo are required before approval.")
    else:
        item.status = "approved"
        item.save(update_fields=["status"])
        messages.success(request, "Approved for eventual eBay publishing (not published).")
    return redirect("batch", pk=item.batch_id)

@login_required
@require_POST
def ai_generate(request, pk):
    item = get_object_or_404(Item, pk=pk, batch__owner=request.user)
    ids = request.POST.getlist('photos')
    if len(ids) != len(set(ids)) or not 1 <= len(ids) <= 10 or any(not v.isdigit() for v in ids):
        messages.error(request, 'Select 1–10 different photographs for AI analysis.')
        return redirect('item', pk=item.pk)
    photos = list(item.photos.filter(pk__in=ids))
    if len(photos) != len(ids):
        messages.error(request, 'Photograph selection is invalid.')
        return redirect('item', pk=item.pk)
    try:
        result = generate(item, photos)
    except AIListingError as exc:
        messages.error(request, str(exc))
        return redirect('item', pk=item.pk)
    with transaction.atomic():
        for field, value in result['fields'].items():
            # Preserve existing user-entered details; AI can fill blanks and regenerate text.
            if field in ('title','description','keywords') or not getattr(item, field):
                setattr(item, field, value[:200] if field == 'keywords' else value)
        item.ai_aspects = result['aspects']
        item.ai_evidence = result['evidence']
        item.status = 'draft'
        item.save()
    messages.success(request, 'AI draft generated. Review all suggested fields before approval.')
    return redirect('item', pk=item.pk)
