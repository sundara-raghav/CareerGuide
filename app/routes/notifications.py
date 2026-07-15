"""Remaining routes — notifications and analytics (separate files)."""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__)
notif_svc = NotificationService()


@notifications_bp.route("/api/unread")
@login_required
def unread():
    notifs = notif_svc.get_unread(current_user.id)
    return jsonify([n.to_dict() for n in notifs])


@notifications_bp.route("/api/mark-read/<int:notif_id>", methods=["POST"])
@login_required
def mark_read(notif_id: int):
    ok = notif_svc.mark_read(notif_id, current_user.id)
    return jsonify({"status": "ok" if ok else "not_found"})
