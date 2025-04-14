from django import forms
from exchange.models import Request, Message


class RequestForm(forms.ModelForm):
    """Form used for CREATING a Request."""

    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Request
        fields = [
            "type",
            "amount",
            "currency",
            "deadline",
            # Status is excluded for creation (defaults to 'active' in model)
            "urgent",
            "hide_contacts",
            "conditions",
        ]
        # Define widgets here so they can be inherited
        widgets = {
            "type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "currency": forms.Select(attrs={"class": "form-select"}),
            # 'deadline' widget defined as a class attribute above
            "urgent": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hide_contacts": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "conditions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class RequestUpdateForm(RequestForm):
    """Form used for UPDATING a Request (inherits from RequestForm)."""

    class Meta(RequestForm.Meta):
        fields = RequestForm.Meta.fields + ["status"]

        # Ensure widgets dict exists and add the status widget
        widgets = RequestForm.Meta.widgets.copy()  # Start with parent's widgets
        widgets["status"] = forms.Select(attrs={"class": "form-select"})


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(
                attrs={
                    "class": "form-control me-2",
                    "placeholder": "Type your message...",
                    "required": "true",
                }
            ),
        }
