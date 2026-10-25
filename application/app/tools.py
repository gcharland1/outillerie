from hashlib import sha256

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app import photos
from app.extensions import db
from models.tool import Tool, ToolCondition

CONDITION_LABELS = {
    ToolCondition.FUNCTIONAL: "Fonctionnel",
    ToolCondition.NEEDS_REPAIR: "À réparer",
    ToolCondition.OUT_OF_ORDER: "Hors d'usage",
}
NAME_MAX_LENGTH = Tool.name.type.length
# A browser never refills a file field, so a redisplayed form must ask for the photo again.
CHOOSE_PHOTO_AGAIN = "Choisissez de nouveau la photo"
CHOOSE_NEW_PHOTO = "Choisissez la nouvelle image"
REPLACE_OR_REMOVE = "Choisissez Modifier l'image ou Retirer l'image, pas les deux"

bp = Blueprint("tools", __name__, url_prefix="/tools")


@bp.context_processor
def inject_condition_labels():
    return {"condition_labels": CONDITION_LABELS}


@bp.route("/mine")
@login_required
def mine():
    return _render_list("tools/mine.html", _my_tools(is_active=True))


@bp.route("/mine/retired")
@login_required
def retired():
    return _render_list("tools/retired.html", _my_tools(is_active=False))


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    values = {}
    if request.method == "POST":
        values, error = _read_tool_form(request.form)
        photo_file = _submitted_photo()
        jpeg, error = _read_photo(error, photo_file)
        if error is None:
            tool = Tool(owner_id=current_user.id, **values)
            if jpeg is not None:
                photos.save_photo(tool, jpeg)
            db.session.add(tool)
            db.session.commit()
            return redirect(url_for("tools.mine"))
        _refuse_form(error, photo_file)
    return render_template(
        "tools/form.html",
        title="Enregistrer un outil",
        action=url_for("tools.new"),
        values=values,
        has_photo=False,
    )


@bp.route("/<int:tool_id>/edit", methods=["GET", "POST"])
@login_required
def edit(tool_id):
    tool = _owned_tool(tool_id)
    if not tool.is_active:
        abort(404)
    values = {
        "name": tool.name,
        "description": tool.description,
        "condition": tool.condition,
        "private_notes": tool.private_notes,
    }
    has_photo = bool(photos.tool_ids_with_photo([tool.id]))
    replace = remove = False
    if request.method == "POST":
        values, error = _read_tool_form(request.form)
        replace = bool(request.form.get("replace_photo"))
        remove = bool(request.form.get("remove_photo"))
        # Decide from the boxes the owner saw: another tab may have changed the photo since.
        form_showed_photo = bool(request.form.get("had_photo"))
        chosen_file = _submitted_photo() if replace or not form_showed_photo else None
        photo_file = None if remove else chosen_file
        if error is None and replace and remove:
            error = REPLACE_OR_REMOVE
        elif error is None and replace and photo_file is None:
            error = CHOOSE_NEW_PHOTO
        elif error is None and photo_file is not None and not replace and has_photo:
            # Opened without a photo, given one since: replacing it takes "Modifier l'image".
            error = CHOOSE_NEW_PHOTO
        jpeg, error = _read_photo(error, photo_file)
        if error is None:
            for field, value in values.items():
                setattr(tool, field, value)
            if jpeg is not None:
                photos.save_photo(tool, jpeg)
            elif remove:
                photos.remove_photo(tool)
            db.session.commit()
            return redirect(url_for("tools.mine"))
        _refuse_form(error, chosen_file)
    return render_template(
        "tools/form.html",
        title="Modifier un outil",
        action=url_for("tools.edit", tool_id=tool.id),
        values=values,
        tool=tool,
        has_photo=has_photo,
        replace_checked=replace,
        remove_checked=remove,
    )


@bp.route("/<int:tool_id>/retire", methods=["GET"])
@login_required
def confirm_retire(tool_id):
    tool = _owned_tool(tool_id)
    if not tool.is_active:
        return _back_from_already_retired()
    return render_template("tools/confirm_retire.html", tool=tool)


@bp.route("/<int:tool_id>/retire", methods=["POST"])
@login_required
def retire(tool_id):
    tool = _owned_tool(tool_id)
    if not tool.is_active:
        return _back_from_already_retired()
    tool.is_active = False
    if request.form.get("erase_private_notes"):
        tool.private_notes = None
    db.session.commit()
    return redirect(url_for("tools.mine"))


@bp.route("/<int:tool_id>/restore", methods=["POST"])
@login_required
def restore(tool_id):
    tool = _owned_tool(tool_id)
    if tool.is_active:
        abort(404)
    tool.is_active = True
    db.session.commit()
    return redirect(url_for("tools.retired"))


@bp.route("/<int:tool_id>/photo")
def photo(tool_id):
    """The tool's photo; the same 404 for a visitor, someone else's tool or no photo"""
    tool = db.session.get(Tool, tool_id)
    if tool is None or not photos.can_view_photo(current_user, tool):
        abort(404)
    stored = photos.load_photo(tool)
    if stored is None:
        abort(404)
    response = Response(stored.content, mimetype=stored.content_type)
    response.set_etag(sha256(stored.content).hexdigest())
    response.cache_control.private = True
    response.cache_control.no_cache = True
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response.make_conditional(request)


def _owned_tool(tool_id):
    """The current user's tool, whatever its state; 404 for anyone else's or an unknown one"""
    tool = db.session.execute(
        select(Tool).where(Tool.id == tool_id, Tool.owner_id == current_user.id)
    ).scalar_one_or_none()
    if tool is None:
        abort(404)
    return tool


def _my_tools(is_active):
    """The current user's tools in or out of circulation, by name regardless of case"""
    return db.session.scalars(
        select(Tool)
        .where(Tool.owner_id == current_user.id, Tool.is_active == is_active)
        .order_by(func.lower(Tool.name), Tool.id)
    ).all()


def _render_list(template, tools):
    photo_ids = photos.tool_ids_with_photo([tool.id for tool in tools])
    return render_template(template, tools=tools, photo_ids=photo_ids)


def _back_from_already_retired():
    """Where Back or a second submit lands after a retire: the list the form was opened from"""
    flash("Cet outil est déjà retiré")
    return redirect(url_for("tools.mine"))


def _submitted_photo():
    """The file chosen in the photo field, or None when the field was left empty"""
    file = request.files.get("photo")
    return file if file and file.filename else None


def _read_photo(form_error, photo_file):
    """The photo ready to store, and the form's refusal message, if any"""
    if form_error is not None or photo_file is None:
        return None, form_error
    try:
        return photos.normalize(photo_file), None
    except photos.PhotoRejected as rejection:
        return None, str(rejection)


def _refuse_form(error, photo_file):
    flash(error)
    if photo_file is not None:
        flash(CHOOSE_PHOTO_AGAIN)


def _read_tool_form(form):
    """Cleaned tool fields from a submitted form, and the message refusing them, if any"""
    values = {
        "name": form.get("name", "").strip(),
        "description": form.get("description", "").strip(),
        "condition": form.get("condition", ToolCondition.FUNCTIONAL.value),
        "private_notes": form.get("private_notes", "").strip() or None,
    }
    if not values["name"] or not values["description"]:
        return values, "Le nom et la description sont obligatoires"
    if len(values["name"]) > NAME_MAX_LENGTH:
        return values, f"Le nom ne doit pas dépasser {NAME_MAX_LENGTH} caractères"
    if values["condition"] not in ToolCondition:
        return values, "L'état choisi est invalide"
    values["condition"] = ToolCondition(values["condition"])
    return values, None
