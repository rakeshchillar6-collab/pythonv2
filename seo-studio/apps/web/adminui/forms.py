# adminui/forms.py
from django import forms
from content.models import Category
from vectorsearch.models import Corpus

class StyledModelForm(forms.ModelForm):
    """A base form to apply consistent styling to all widgets."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.Textarea, forms.Select, forms.EmailInput)):
                widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'})

class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'parent']

class CorpusForm(StyledModelForm):
    class Meta:
        model = Corpus
        fields = ['site', 'name', 'description', 'lang', 'content_type', 'source', 'is_active']
