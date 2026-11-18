from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["brand", "item_type", "gender", "size", "colour", "keywords",
                  "title", "description", "condition_notes", "price", "purchase_cost",
                  "storage_location"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4}),
                   "condition_notes": forms.Textarea(attrs={"rows": 3})}
    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) > 80:
            raise forms.ValidationError("eBay titles cannot exceed 80 characters.")
        return title

# Category-specific suggestions remain editable and are never silently published.
from .ai_service import ASPECTS
for _aspect in ASPECTS:
    ItemForm.base_fields['aspect_' + _aspect] = forms.CharField(required=False, label=_aspect.replace('_', ' ').title(), max_length=500)
_old_init = ItemForm.__init__
def _itemform_init(self, *args, **kwargs):
    _old_init(self, *args, **kwargs)
    if self.instance and self.instance.pk:
        for key in ASPECTS:
            self.fields['aspect_' + key].initial = str(self.instance.ai_aspects.get(key) or '')
ItemForm.__init__ = _itemform_init
