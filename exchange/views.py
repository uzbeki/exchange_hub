from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import ContextMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import (
    TemplateView,
    View,
    RedirectView,
    DeleteView,
    UpdateView,
    CreateView,
)
import json
from django.urls import reverse, reverse_lazy
from exchange.models import (
    Conversation,
    Request,
    Message,
    LuggageListing,
    LuggageReservation,
    LuggageTelegramSubscription,
    TelegramLinkToken,
)
from exchange.forms import (
    RequestForm,
    MessageForm,
    RequestUpdateForm,
    LuggageListingForm,
    LuggageReservationForm,
)
from django.contrib import messages
from django.db import models
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from exchange.notifications import notify_listing_subscribers
from exchange.telegram import (
    bot_start_url,
    bot_chat_url,
    create_telegram_link_token,
    send_telegram_message,
    verify_webhook_secret,
)


class BaseMixin(LoginRequiredMixin, ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_messages"] = Message.get_unread_message_count_by_user(self.request.user)
        return context


def _build_telegram_connect_url(user) -> str:
    if user.telegram_chat_id:
        return bot_chat_url()

    token_obj = (
        TelegramLinkToken.objects.filter(
            user=user,
            used_at__isnull=True,
            expires_at__gte=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )
    if not token_obj:
        token_obj = create_telegram_link_token(user)

    return bot_start_url(token_obj.token) or bot_chat_url()


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


class LuggageMarketplaceView(TemplateView):
    template_name = "exchange/luggage_marketplace.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["listings"] = LuggageListing.objects.filter(is_active=True).select_related(
            "seller"
        )
        context["unread_messages"] = (
            Message.get_unread_message_count_by_user(self.request.user)
            if self.request.user.is_authenticated
            else 0
        )
        return context


class LuggageListingCreateView(LoginRequiredMixin, CreateView):
    template_name = "exchange/luggage_listing_form.html"
    model = LuggageListing
    form_class = LuggageListingForm
    success_url = reverse_lazy("luggage_my_listings")

    def form_valid(self, form):
        form.instance.seller = self.request.user
        messages.success(self.request, _("Luggage storage listing published."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = _("Create Luggage Storage Listing")
        context["submit_button_text"] = _("Publish Listing")
        context["unread_messages"] = Message.get_unread_message_count_by_user(
            self.request.user
        )
        return context


class LuggageListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "exchange/luggage_listing_form.html"
    model = LuggageListing
    form_class = LuggageListingForm
    pk_url_kwarg = "listing_id"
    success_url = reverse_lazy("luggage_my_listings")

    def test_func(self):
        return self.get_object().seller == self.request.user

    def form_valid(self, form):
        messages.success(self.request, _("Luggage listing updated."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = _("Edit Luggage Storage Listing")
        context["submit_button_text"] = _("Save Changes")
        context["unread_messages"] = Message.get_unread_message_count_by_user(
            self.request.user
        )
        return context


class DeleteLuggageListingView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        listing = get_object_or_404(LuggageListing, id=kwargs["listing_id"])
        if listing.seller != request.user:
            messages.error(request, _("You are not allowed to delete this listing."))
            return redirect("luggage_listing_detail", listing_id=listing.id)

        listing.delete()
        messages.success(request, _("Luggage listing deleted."))
        return redirect("luggage_my_listings")


class ToggleLuggageListingActiveView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        listing = get_object_or_404(LuggageListing, id=kwargs["listing_id"])
        if listing.seller != request.user:
            messages.error(request, _("You are not allowed to update this listing."))
            return redirect("luggage_listing_detail", listing_id=listing.id)

        action = request.POST.get("action")
        if action == "close":
            listing.is_active = False
            messages.success(request, _("Listing marked as done/closed."))
        elif action == "reopen":
            listing.is_active = True
            messages.success(request, _("Listing reopened."))
        else:
            messages.error(request, _("Invalid listing action."))
            return redirect("luggage_listing_detail", listing_id=listing.id)

        listing.save(update_fields=["is_active", "updated_at"])

        next_url = request.POST.get("next")
        if next_url == "my_listings":
            return redirect("luggage_my_listings")
        return redirect("luggage_listing_detail", listing_id=listing.id)


class MyLuggageListingsView(LoginRequiredMixin, TemplateView):
    template_name = "exchange/my_luggage_listings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["listings"] = (
            LuggageListing.objects.filter(seller=self.request.user)
            .prefetch_related("reservations__buyer")
            .order_by("-created_at")
        )
        context["unread_messages"] = Message.get_unread_message_count_by_user(
            self.request.user
        )
        return context


class LuggageListingDetailView(TemplateView):
    template_name = "exchange/luggage_listing_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = get_object_or_404(LuggageListing, id=self.kwargs["listing_id"])
        context["listing"] = listing
        context["reservations"] = listing.reservations.select_related("buyer")
        context["reservation_form"] = LuggageReservationForm(listing=listing)
        if self.request.user.is_authenticated:
            context["telegram_subscription"] = LuggageTelegramSubscription.objects.filter(
                listing=listing,
                user=self.request.user,
            ).first()
            context["telegram_is_linked"] = bool(self.request.user.telegram_chat_id)
            context["telegram_link_url"] = _build_telegram_connect_url(self.request.user)
        context["unread_messages"] = (
            Message.get_unread_message_count_by_user(self.request.user)
            if self.request.user.is_authenticated
            else 0
        )
        return context


class ToggleLuggageTelegramSubscriptionView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        listing = get_object_or_404(LuggageListing, id=kwargs["listing_id"])

        if not request.user.telegram_chat_id:
            link_url = _build_telegram_connect_url(request.user)
            if link_url:
                messages.info(
                    request,
                    _("First connect Telegram: open %(url)s from this account, then return here.")
                    % {"url": link_url},
                )
            else:
                messages.error(
                    request,
                    _("Telegram bot username is not configured by admin yet."),
                )
            return redirect("luggage_listing_detail", listing_id=listing.id)

        subscription, _created = LuggageTelegramSubscription.objects.get_or_create(
            user=request.user,
            listing=listing,
            defaults={
                "is_active": True,
                "notify_on_new_reservation": True,
                "notify_on_status_change": True,
                "notify_on_sold_out": True,
                "notify_on_reopened": True,
            },
        )

        action = request.POST.get("action", "save")
        if action == "disable":
            subscription.is_active = False
        else:
            subscription.is_active = request.POST.get("is_active") == "on"
            subscription.notify_on_new_reservation = (
                request.POST.get("notify_on_new_reservation") == "on"
            )
            subscription.notify_on_status_change = (
                request.POST.get("notify_on_status_change") == "on"
            )
            subscription.notify_on_sold_out = request.POST.get("notify_on_sold_out") == "on"
            subscription.notify_on_reopened = request.POST.get("notify_on_reopened") == "on"

        subscription.save()

        if subscription.is_active:
            messages.success(request, _("Telegram notification settings saved."))
        else:
            messages.success(request, _("Telegram notifications disabled for this listing."))

        return redirect("luggage_listing_detail", listing_id=listing.id)


class LuggageNotificationsView(LoginRequiredMixin, TemplateView):
    template_name = "exchange/luggage_notifications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscriptions"] = (
            LuggageTelegramSubscription.objects.filter(user=self.request.user)
            .select_related("listing")
            .order_by("-updated_at")
        )
        context["telegram_is_linked"] = bool(self.request.user.telegram_chat_id)
        context["telegram_link_url"] = _build_telegram_connect_url(self.request.user)
        context["unread_messages"] = Message.get_unread_message_count_by_user(
            self.request.user
        )
        return context


class UpdateLuggageNotificationView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        subscription = get_object_or_404(
            LuggageTelegramSubscription,
            id=kwargs["subscription_id"],
            user=request.user,
        )

        action = request.POST.get("action", "save")
        if action == "disable":
            subscription.is_active = False
        elif action == "enable":
            subscription.is_active = True
        else:
            subscription.is_active = request.POST.get("is_active") == "on"
            subscription.notify_on_new_reservation = (
                request.POST.get("notify_on_new_reservation") == "on"
            )
            subscription.notify_on_status_change = (
                request.POST.get("notify_on_status_change") == "on"
            )
            subscription.notify_on_sold_out = request.POST.get("notify_on_sold_out") == "on"
            subscription.notify_on_reopened = request.POST.get("notify_on_reopened") == "on"

        subscription.save()
        messages.success(request, _("Notification settings updated."))
        return redirect("luggage_notifications")


class CreateLuggageReservationView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        listing = get_object_or_404(LuggageListing, id=kwargs["listing_id"])
        was_sold_out = listing.remaining_kg <= 0

        if listing.seller == request.user:
            messages.error(request, _("You cannot reserve your own listing."))
            return redirect("luggage_listing_detail", listing_id=listing.id)

        reservation = LuggageReservation(listing=listing, buyer=request.user)
        form = LuggageReservationForm(request.POST, instance=reservation, listing=listing)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.buyer = request.user
            try:
                reservation.clean()
                reservation.save()
                listing.refresh_from_db()
                notify_listing_subscribers(
                    listing,
                    event="reservation_created",
                    reservation=reservation,
                )
                if not was_sold_out and listing.remaining_kg <= 0:
                    notify_listing_subscribers(listing, event="sold_out")
                messages.success(
                    request,
                    _("Reservation submitted. Contact the seller to complete payment and handover."),
                )
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field_name, errors in exc.message_dict.items():
                        for error in errors:
                            messages.error(request, error)
                else:
                    for error in exc.messages:
                        messages.error(request, error)
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)

        return redirect("luggage_listing_detail", listing_id=listing.id)


class UpdateLuggageReservationStatusView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        reservation = get_object_or_404(LuggageReservation, id=kwargs["reservation_id"])
        listing = reservation.listing
        was_sold_out = listing.remaining_kg <= 0
        previous_status = reservation.status

        if listing.seller != request.user:
            messages.error(request, _("You are not allowed to update this reservation."))
            return redirect("luggage_listing_detail", listing_id=listing.id)

        next_status = request.POST.get("status")
        allowed_statuses = {
            LuggageReservation.STATUS_PENDING,
            LuggageReservation.STATUS_RESERVED,
            LuggageReservation.STATUS_CANCELLED,
        }
        if next_status not in allowed_statuses:
            messages.error(request, _("Invalid reservation status."))
            return redirect("luggage_listing_detail", listing_id=listing.id)

        reservation.status = next_status
        try:
            reservation.clean()
            reservation.save(update_fields=["status", "updated_at"])
            listing.refresh_from_db()
            notify_listing_subscribers(
                listing,
                event="reservation_status_changed",
                reservation=reservation,
                previous_status=previous_status,
            )
            is_sold_out = listing.remaining_kg <= 0
            if not was_sold_out and is_sold_out:
                notify_listing_subscribers(listing, event="sold_out")
            if was_sold_out and not is_sold_out:
                notify_listing_subscribers(listing, event="reopened")
            messages.success(request, _("Reservation status updated."))
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field_name, errors in exc.message_dict.items():
                    for error in errors:
                        messages.error(request, error)
            else:
                for error in exc.messages:
                    messages.error(request, error)
        return redirect("luggage_listing_detail", listing_id=listing.id)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        if not verify_webhook_secret(request):
            return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"ok": True})

        message_obj = payload.get("message") or payload.get("edited_message") or {}
        text = (message_obj.get("text") or "").strip()
        chat = message_obj.get("chat") or {}
        from_user = message_obj.get("from") or {}
        chat_id = chat.get("id")
        username = from_user.get("username") or ""

        if not text or not chat_id:
            return JsonResponse({"ok": True})

        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            start_token = parts[1].strip() if len(parts) > 1 else ""

            if start_token:
                token_obj = TelegramLinkToken.objects.select_related("user").filter(
                    token=start_token
                ).first()
                if not token_obj:
                    send_telegram_message(
                        str(chat_id),
                        "Invalid or unknown connect token. Please click Connect Telegram again from the website.",
                    )
                    return JsonResponse({"ok": True})

                if not token_obj.is_valid:
                    send_telegram_message(
                        str(chat_id),
                        "This connect token is expired or already used. Please generate a new one from the website.",
                    )
                    return JsonResponse({"ok": True})

                user = token_obj.user

                get_user_model().objects.filter(telegram_chat_id=str(chat_id)).exclude(
                    pk=user.pk
                ).update(
                    telegram_chat_id=None,
                    telegram_username="",
                    telegram_notifications_enabled=False,
                    telegram_linked_at=None,
                )

                user.link_telegram(chat_id=str(chat_id), username=username)
                user.save(
                    update_fields=[
                        "telegram_chat_id",
                        "telegram_username",
                        "telegram_notifications_enabled",
                        "telegram_linked_at",
                    ]
                )
                token_obj.used_at = timezone.now()
                token_obj.save(update_fields=["used_at"])

                send_telegram_message(
                    str(chat_id),
                    f"Connected ✅ This Telegram chat is now linked to {user.username}.",
                )
                return JsonResponse({"ok": True})

            send_telegram_message(
                str(chat_id),
                "Welcome! Open the website and use the Connect Telegram button to link this chat securely. Use /help for commands.",
            )
            return JsonResponse({"ok": True})

        linked_user = get_user_model().objects.filter(telegram_chat_id=str(chat_id)).first()

        if text.startswith("/connect"):
            send_telegram_message(
                str(chat_id),
                "For security, /connect is deprecated. Please tap Connect Telegram on the website, which opens this bot with a one-time token.",
            )
            return JsonResponse({"ok": True})

        if not linked_user:
            send_telegram_message(
                str(chat_id),
                "This chat is not linked yet. Open the website and press Connect Telegram.",
            )
            return JsonResponse({"ok": True})

        if text.startswith("/help"):
            send_telegram_message(
                str(chat_id),
                "Commands:\n"
                "/status - connection and global notification status\n"
                "/subscriptions - list your listing subscriptions\n"
                "/mute_all - pause all Telegram notifications\n"
                "/unmute_all - resume notifications\n"
                "/unsubscribe <id> - disable one subscription\n"
                "/subscribe <id> - enable one subscription\n"
                "/unsubscribe_all - disable all listing subscriptions\n"
                "/stop - pause global notifications",
            )
            return JsonResponse({"ok": True})

        if text.startswith("/status"):
            active_count = LuggageTelegramSubscription.objects.filter(
                user=linked_user, is_active=True
            ).count()
            send_telegram_message(
                str(chat_id),
                f"Linked as {linked_user.username}.\n"
                f"Global notifications: {'ON' if linked_user.telegram_notifications_enabled else 'OFF'}\n"
                f"Active listing subscriptions: {active_count}",
            )
            return JsonResponse({"ok": True})

        if text.startswith("/mute_all") or text.startswith("/stop"):
            linked_user.telegram_notifications_enabled = False
            linked_user.save(update_fields=["telegram_notifications_enabled"])
            send_telegram_message(str(chat_id), "Global Telegram notifications paused.")
            return JsonResponse({"ok": True})

        if text.startswith("/unmute_all"):
            linked_user.telegram_notifications_enabled = True
            linked_user.save(update_fields=["telegram_notifications_enabled"])
            send_telegram_message(str(chat_id), "Global Telegram notifications resumed.")
            return JsonResponse({"ok": True})

        if text.startswith("/subscriptions"):
            subs = LuggageTelegramSubscription.objects.filter(user=linked_user).select_related(
                "listing"
            )[:20]
            if not subs:
                send_telegram_message(str(chat_id), "You have no listing subscriptions yet.")
            else:
                lines = ["Your subscriptions:"]
                for sub in subs:
                    lines.append(
                        f"#{sub.id} {'✅' if sub.is_active else '⏸'} {sub.listing.title}"
                    )
                send_telegram_message(str(chat_id), "\n".join(lines))
            return JsonResponse({"ok": True})

        if text.startswith("/unsubscribe_all"):
            LuggageTelegramSubscription.objects.filter(user=linked_user).update(
                is_active=False
            )
            send_telegram_message(str(chat_id), "All listing subscriptions disabled.")
            return JsonResponse({"ok": True})

        if text.startswith("/unsubscribe"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].isdigit():
                send_telegram_message(str(chat_id), "Usage: /unsubscribe <subscription_id>")
                return JsonResponse({"ok": True})
            sub = LuggageTelegramSubscription.objects.filter(
                id=int(parts[1]), user=linked_user
            ).first()
            if not sub:
                send_telegram_message(str(chat_id), "Subscription not found.")
                return JsonResponse({"ok": True})
            sub.is_active = False
            sub.save(update_fields=["is_active", "updated_at"])
            send_telegram_message(str(chat_id), f"Disabled subscription #{sub.id}.")
            return JsonResponse({"ok": True})

        if text.startswith("/subscribe"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].isdigit():
                send_telegram_message(str(chat_id), "Usage: /subscribe <subscription_id>")
                return JsonResponse({"ok": True})
            sub = LuggageTelegramSubscription.objects.filter(
                id=int(parts[1]), user=linked_user
            ).first()
            if not sub:
                send_telegram_message(str(chat_id), "Subscription not found.")
                return JsonResponse({"ok": True})
            sub.is_active = True
            sub.save(update_fields=["is_active", "updated_at"])
            send_telegram_message(str(chat_id), f"Enabled subscription #{sub.id}.")
            return JsonResponse({"ok": True})

        send_telegram_message(str(chat_id), "Unknown command. Send /help for available commands.")

        return JsonResponse({"ok": True})


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
