from django import forms
from exchange.models import Request, Message, LuggageListing, LuggageReservation


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
                    "autofocus": "true",
                    "autocomplete": "off",
                }
            ),
        }


class LuggageListingForm(forms.ModelForm):
    available_until = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"},
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d"],
    )
    arrival_datetime = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = LuggageListing
        fields = [
            "title",
            "total_kg",
            "price_per_kg",
            "price_currency",
            "available_until",
            "arrival_datetime",
            "departure_city",
            "arrival_city",
            "pickup_location_tokyo",
            "delivery_options",
            "allowed_items",
            "prohibited_items",
            "description",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "total_kg": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "price_per_kg": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "price_currency": forms.Select(attrs={"class": "form-select"}),
            "departure_city": forms.TextInput(attrs={"class": "form-control"}),
            "arrival_city": forms.TextInput(attrs={"class": "form-control"}),
            "pickup_location_tokyo": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "delivery_options": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "allowed_items": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "prohibited_items": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class LuggageReservationForm(forms.ModelForm):
    class Meta:
        model = LuggageReservation
        fields = ["kg_requested", "contact_handle", "note"]
        widgets = {
            "kg_requested": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "contact_handle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number (optional)",
                }
            ),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing

    def clean(self):
        cleaned_data = super().clean()
        if not self.listing:
            return cleaned_data

        reservation = self.instance
        reservation.listing = self.listing
        reservation.kg_requested = cleaned_data.get("kg_requested")
        if reservation.kg_requested:
            reservation.clean()
        return cleaned_data
