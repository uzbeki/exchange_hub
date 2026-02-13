from django.db.models import Q

from exchange.models import LuggageTelegramSubscription
from exchange.telegram import send_telegram_message


def notify_listing_subscribers(
    listing,
    event: str,
    reservation=None,
    previous_status: str = "",
):
    filters = Q(is_active=True, listing=listing)
    if event == "reservation_created":
        filters &= Q(notify_on_new_reservation=True)
    elif event == "reservation_status_changed":
        filters &= Q(notify_on_status_change=True)
    elif event == "sold_out":
        filters &= Q(notify_on_sold_out=True)
    elif event == "reopened":
        filters &= Q(notify_on_reopened=True)

    subscriptions = (
        LuggageTelegramSubscription.objects.select_related("user")
        .filter(filters)
    )

    for subscription in subscriptions:
        user = subscription.user
        if not user.telegram_notifications_enabled or not user.telegram_chat_id:
            continue
        message = _build_message(
            listing=listing,
            event=event,
            reservation=reservation,
            previous_status=previous_status,
        )
        send_telegram_message(user.telegram_chat_id, message)


def _build_message(listing, event: str, reservation=None, previous_status: str = "") -> str:
    base = (
        f"📦 Luggage listing update\n"
        f"Listing: {listing.title}\n"
        f"Route: {listing.departure_city} → {listing.arrival_city}\n"
        f"Remaining: {listing.remaining_kg}kg"
    )

    if event == "reservation_created" and reservation is not None:
        return (
            f"{base}\n\n"
            f"🆕 New reservation: {reservation.kg_requested}kg by {reservation.buyer.username}."
        )

    if event == "reservation_status_changed" and reservation is not None:
        return (
            f"{base}\n\n"
            f"🔄 Reservation updated: {reservation.kg_requested}kg for {reservation.buyer.username} "
            f"({previous_status} → {reservation.status})."
        )

    if event == "sold_out":
        return f"{base}\n\n✅ This listing is now sold out."

    if event == "reopened":
        return f"{base}\n\n♻️ Space became available again."

    return f"{base}\n\nℹ️ Listing changed."
