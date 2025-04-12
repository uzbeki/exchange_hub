from django import forms
from exchange.models import Request, Message


class RequestForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )

    class Meta:
        model = Request
        fields = [
            "type",
            "amount",
            "currency",
            "deadline",
            "status",
            "urgent",
            "hide_contacts",
            "conditions",
        ]


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
