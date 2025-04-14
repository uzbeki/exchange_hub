from django import forms
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import ContextMixin
from django.views.generic import (
    TemplateView,
    View,
    RedirectView,
    DeleteView,
    UpdateView,
    CreateView,
)
from django.urls import reverse, reverse_lazy
from exchange.models import Conversation, Request, Message
from exchange.forms import RequestForm, MessageForm, RequestUpdateForm
from django.contrib import messages
from django.db import models
from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext_lazy as _


class BaseMixin(LoginRequiredMixin, ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_messages"] = Message.get_unread_message_count_by_user(self.request.user)
        return context


class CreateOfferView(BaseMixin, CreateView):
    model = Request
    form_class = RequestForm
    template_name = "exchange/offer_form.html"  # Unified template
    success_url = reverse_lazy("my_offers")  # Or reverse_lazy("home")

    def form_valid(self, form):
        # Assign the user before saving
        form.instance.user = self.request.user
        messages.success(self.request, _("New offer created successfully"))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = _("Create an Offer")
        context["submit_button_text"] = _("Create Offer")
        return context


class UpdateOfferView(BaseMixin, UserPassesTestMixin, UpdateView):
    model = Request
    form_class = RequestUpdateForm  # Use the specific update form class
    template_name = "exchange/offer_form.html"
    pk_url_kwarg = "request_id"
    success_url = reverse_lazy("my_offers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = _("Update Your Offer")
        context["submit_button_text"] = _("Update Offer")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Offer updated successfully"))
        return super().form_valid(form)

    def test_func(self):
        req = self.get_object()
        return req.user == self.request.user


class CompleteRequestView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        req = get_object_or_404(
            Request, id=kwargs["request_id"], user=self.request.user
        )
        if req.status == "active":
            req.status = "completed"
            req.save()
            messages.success(self.request, _("Offer completed successfully"))
        return reverse("my_offers")

    def test_func(self):
        # Check if the user is the owner of the request
        req = get_object_or_404(Request, id=self.kwargs["request_id"])
        return req.user == self.request.user


class DeleteRequestView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Request
    success_url = reverse_lazy("my_offers")
    pk_url_kwarg = "request_id"

    def form_valid(self, form):
        messages.success(self.request, _("Offer deleted successfully"))
        return super().form_valid(form)

    def test_func(self):
        # Check if the user is the owner of the request
        return self.get_object().user == self.request.user


class MyRequestsView(BaseMixin, TemplateView):
    template_name = "exchange/my_offers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["requests"] = Request.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        return context


class StartConversationView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, request_id, *args, **kwargs):
        req = get_object_or_404(Request, id=request_id)
        if self.request.user == req.user:
            return redirect("home")

        conversation = (
            Conversation.objects.filter(
                request=req, participant1=self.request.user, participant2=req.user
            ).first()
            or Conversation.objects.filter(
                request=req, participant1=req.user, participant2=req.user
            ).first()
        )

        if not conversation:
            conversation = Conversation.objects.create(
                request=req, participant1=self.request.user, participant2=req.user
            )

        return redirect("conversation", conversation_id=conversation.id)


class ConversationsListView(BaseMixin, TemplateView):
    template_name = "exchange/conversations_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["conversations"] = Conversation.get_user_conversations(
            self.request.user
        )
        return context


class ConversationView(BaseMixin, UserPassesTestMixin, TemplateView):
    template_name = "exchange/conversation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = Conversation.objects.get(id=self.kwargs["conversation_id"])
        messages = conversation.messages.all()
        messages.filter(~models.Q(sender=self.request.user)).update(is_read=True)

        context["conversation"] = conversation
        context["conversations"] = Conversation.get_user_conversations(
            self.request.user
        )
        context["chat_messages"] = messages
        context["form"] = MessageForm()
        return context

    def post(self, request: HttpRequest, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation, id=self.kwargs["conversation_id"]
        )
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
        return redirect("conversation", conversation_id=conversation.id)

    def test_func(self):
        """Check if the user is a participant in the conversation"""
        conversation = get_object_or_404(
            Conversation, id=self.kwargs["conversation_id"]
        )
        return self.request.user in [
            conversation.participant1,
            conversation.participant2,
        ]


class DeleteConversationView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        try:
            conversation = Conversation.objects.get(id=self.kwargs["conversation_id"])
        except Conversation.DoesNotExist:
            return JsonResponse(
                {"error": "Conversation not found."},
                status=404,
            )
        # Check if the user is a participant in the conversation
        if request.user not in [
            conversation.participant1,
            conversation.participant2,
        ]:
            return JsonResponse(
                {"error": "You are not authorized to delete this conversation."},
                status=403,
            )
        conversation.delete()
        messages.success(request, _("Conversation deleted successfully."))
        return JsonResponse(
            {
                "success": _("Conversation deleted successfully."),
                "redirect_url": reverse("conversations_list"),
            }
        )
