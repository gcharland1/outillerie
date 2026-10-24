from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app.extensions import db
from models.tool import Tool, ToolCondition

CONDITION_LABELS = {
    ToolCondition.FUNCTIONAL: "Fonctionnel",
    ToolCondition.NEEDS_REPAIR: "À réparer",
    ToolCondition.OUT_OF_ORDER: "Hors d'usage",
}
NAME_MAX_LENGTH = Tool.name.type.length

bp = Blueprint("tools", __name__, url_prefix="/tools")


@bp.context_processor
def inject_condition_labels():
    return {"condition_labels": CONDITION_LABELS}


@bp.route("/mine")
@login_required
def mine():
    return render_template("tools/mine.html", tools=_my_tools(is_active=True))


@bp.route("/mine/retired")
@login_required
def retired():
    return render_template("tools/retired.html", tools=_my_tools(is_active=False))


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    values = {}
    if request.method == "POST":
        values, error = _read_tool_form(request.form)
        if error is None:
            db.session.add(Tool(owner_id=current_user.id, **values))
            db.session.commit()
            return redirect(url_for("tools.mine"))
        flash(error)
    return render_template(
        "tools/form.html", title="Enregistrer un outil", action=url_for("tools.new"), values=values
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
    if request.method == "POST":
        values, error = _read_tool_form(request.form)
        if error is None:
            for field, value in values.items():
                setattr(tool, field, value)
            db.session.commit()
            return redirect(url_for("tools.mine"))
        flash(error)
    return render_template(
        "tools/form.html",
        title="Modifier un outil",
        action=url_for("tools.edit", tool_id=tool.id),
        values=values,
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


def _back_from_already_retired():
    """Where Back or a second submit lands after a retire: the list the form was opened from"""
    flash("Cet outil est déjà retiré")
    return redirect(url_for("tools.mine"))


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
