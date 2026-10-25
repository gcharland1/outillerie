import ast
import re
from html import unescape
from io import BytesIO
from pathlib import Path

import pytest
from flask_login import AnonymousUserMixin
from PIL import ExifTags, Image
from sqlalchemy import event
from werkzeug.datastructures import FileStorage

from app import photos
from app.extensions import db
from app.photos import PhotoRejected, normalize
from models import Tool, ToolPhoto, User
from tests.conftest import (
    USER_PASSWORD,
    a_photo,
    add_tool,
    encoded,
    log_in_with_page_token,
    stored,
    token_in,
    tool_count,
    tool_form,
)
from tests.factories import make_tool, make_user

REPLACE = "Modifier l'image"
REMOVE = "Retirer l'image"
ADD = "Ajouter une image"
REMOVAL_WARNING = 'Retirer l\'image <span class="photo-warning">(définitif)</span>'


def page_text(response):
    return unescape(response.get_data(as_text=True))


def upload(data, filename="photo.jpg"):
    return FileStorage(stream=BytesIO(data), filename=filename)


def opened(jpeg_bytes):
    return Image.open(BytesIO(jpeg_bytes))


def refusal(data, filename="photo.jpg"):
    with pytest.raises(PhotoRejected) as refused:
        normalize(upload(data, filename))
    return str(refused.value)


def test_gif_is_refused(gif_image):
    assert refusal(gif_image, "photo.gif") == photos.WRONG_FORMAT


def test_text_named_like_a_jpeg_is_refused():
    assert refusal(b"Ceci n'est pas une image", "perceuse.jpg") == photos.WRONG_FORMAT


def test_truncated_jpeg_is_unreadable(truncated_jpeg):
    assert refusal(truncated_jpeg) == photos.UNREADABLE


def test_empty_file_is_unreadable():
    assert refusal(b"") == photos.UNREADABLE


def test_file_over_10_mb_is_refused_before_being_decoded():
    assert refusal(b"\0" * (11 * 1024 * 1024)) == photos.TOO_HEAVY


@pytest.mark.filterwarnings("ignore::PIL.Image.DecompressionBombWarning")
def test_image_over_40_million_pixels_is_refused(huge_png):
    assert refusal(huge_png, "photo.png") == photos.TOO_LARGE


@pytest.mark.parametrize("fixture", ["jpeg_photo", "transparent_png", "webp_photo"])
def test_accepted_formats_are_stored_as_jpeg(request, fixture):
    image = opened(normalize(upload(request.getfixturevalue(fixture))))

    assert image.format == "JPEG"


def test_large_photo_is_reduced_to_1600_pixels(large_geotagged_photo):
    image = opened(normalize(upload(large_geotagged_photo)))

    assert image.size == (1600, 1200)


def test_small_photo_is_not_enlarged():
    image = opened(normalize(upload(encoded(a_photo((800, 600)), "PNG"), "photo.png")))

    assert image.size == (800, 600)


def test_metadata_and_gps_position_are_removed(large_geotagged_photo):
    assert opened(large_geotagged_photo).getexif().get_ifd(ExifTags.IFD.GPSInfo)

    image = opened(normalize(upload(large_geotagged_photo)))

    assert not image.getexif()
    assert "exif" not in image.info


def test_orientation_is_applied(sideways_photo):
    image = opened(normalize(upload(sideways_photo)))

    assert image.size == (1200, 1600)


def test_transparent_areas_become_white(transparent_png):
    image = opened(normalize(upload(transparent_png, "photo.png")))

    red, green, blue = image.getpixel((10, 10))
    assert min(red, green, blue) > 245


@pytest.fixture
def owner(mock_app):
    with mock_app.app_context():
        user = make_user("alice", "alice@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


def test_saved_photo_replaces_the_previous_one(mock_app, owner):
    with mock_app.app_context():
        tool = make_tool(owner)
        photos.save_photo(tool, b"first")
        db.session.commit()
        photos.save_photo(tool, b"second")
        db.session.commit()
        db.session.expunge_all()

        stored = ToolPhoto.query.all()
        assert [(p.content, p.content_type) for p in stored] == [(b"second", "image/jpeg")]


def test_removing_a_photo_twice_is_harmless(mock_app, owner):
    with mock_app.app_context():
        tool = make_tool(owner)
        photos.save_photo(tool, b"photo")
        db.session.commit()

        photos.remove_photo(tool)
        db.session.commit()
        photos.remove_photo(tool)
        db.session.commit()

        assert ToolPhoto.query.count() == 0
        assert photos.load_photo(db.session.get(Tool, tool.id)) is None


def test_tool_ids_with_photo_reads_no_photo_content(mock_app, owner):
    with mock_app.app_context():
        with_photo = make_tool(owner, name="Perceuse")
        without_photo = make_tool(owner, name="Scie")
        photos.save_photo(with_photo, b"photo")
        db.session.commit()
        statements = []
        event.listen(db.engine, "before_cursor_execute", lambda *args: statements.append(args[2]))

        found = photos.tool_ids_with_photo([with_photo.id, without_photo.id])

        assert found == {with_photo.id}
        assert statements and not any("content" in sql for sql in statements)


def test_only_the_owner_can_view_a_photo(mock_app, owner):
    with mock_app.app_context():
        neighbour = make_user("bob", "bob@example.com")
        db.session.add(neighbour)
        db.session.commit()
        tool = make_tool(owner)

        assert photos.can_view_photo(db.session.get(User, owner), tool)
        assert not photos.can_view_photo(neighbour, tool)
        assert not photos.can_view_photo(AnonymousUserMixin(), tool)


def photo_access_outside_the_photo_module():
    """`ToolPhoto` or `.photo` used in the app's code anywhere but app/photos.py (ADR 0008)"""
    app_dir = Path(photos.__file__).parent
    found = []
    for path in sorted(app_dir.glob("*.py")):
        if path.name == "photos.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(), str(path))):
            if (isinstance(node, ast.Name) and node.id == "ToolPhoto") or (
                isinstance(node, ast.Attribute) and node.attr == "photo"
            ):
                found.append(f"{path.name}:{node.lineno}")
    return found


def test_only_the_photo_module_touches_photos():
    assert photo_access_outside_the_photo_module() == []


def give_photo(mock_app, tool_id, data):
    with mock_app.app_context():
        photos.save_photo(db.session.get(Tool, tool_id), normalize(upload(data)))
        db.session.commit()


def photo_url(tool_id):
    return f"/tools/{tool_id}/photo"


def test_owner_gets_the_photo(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    response = logged_in_client.get(photo_url(tool_id))

    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    assert opened(response.get_data()).format == "JPEG"


def test_owner_gets_the_photo_of_a_retired_tool(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id, is_active=False)
    give_photo(mock_app, tool_id, jpeg_photo)

    assert logged_in_client.get(photo_url(tool_id)).status_code == 200


def test_neighbour_gets_404(mock_app, logged_in_client, bob_id, jpeg_photo):
    tool_id = add_tool(mock_app, bob_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    assert logged_in_client.get(photo_url(tool_id)).status_code == 404


def test_visitor_gets_404(mock_app, client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    assert client.get(photo_url(tool_id)).status_code == 404


def test_tool_without_photo_gets_404(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    assert logged_in_client.get(photo_url(tool_id)).status_code == 404


def test_unknown_tool_gets_404(logged_in_client):
    assert logged_in_client.get(photo_url(999_999)).status_code == 404


def test_photo_is_cached_privately_and_not_sniffed(
    mock_app, logged_in_client, alice_id, jpeg_photo
):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    response = logged_in_client.get(photo_url(tool_id))

    assert response.headers["Cache-Control"] == "private, no-cache"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["ETag"]


def test_unchanged_photo_is_not_sent_again(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    etag = logged_in_client.get(photo_url(tool_id)).headers["ETag"]

    response = logged_in_client.get(photo_url(tool_id), headers={"If-None-Match": etag})

    assert response.status_code == 304
    assert response.get_data() == b""


def test_replaced_photo_is_sent_despite_the_old_etag(
    mock_app, logged_in_client, alice_id, jpeg_photo
):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    old = logged_in_client.get(photo_url(tool_id))
    give_photo(mock_app, tool_id, encoded(a_photo((640, 480)), "PNG"))

    response = logged_in_client.get(
        photo_url(tool_id), headers={"If-None-Match": old.headers["ETag"]}
    )

    assert response.status_code == 200
    assert response.get_data() != old.get_data()


def photo_of(mock_app, tool_id):
    """The stored photo's bytes, or None"""
    with mock_app.app_context():
        stored_photo = db.session.get(ToolPhoto, tool_id)
        return None if stored_photo is None else stored_photo.content


def with_file(data, filename="photo.jpg", **fields):
    return {**tool_form(**fields), "photo": (BytesIO(data), filename)}


def post_form(client, url, data):
    return client.post(url, data=data, content_type="multipart/form-data")


def edit_url(tool_id):
    return f"/tools/{tool_id}/edit"


def edit_with_photo(client, tool_id, data):
    """Submits the edit form as shown for a tool that has a photo"""
    return post_form(client, edit_url(tool_id), {**data, "had_photo": "1"})


@pytest.mark.parametrize("url", ["/tools/new", "edit"])
def test_forms_offer_a_photo_field(mock_app, logged_in_client, alice_id, url):
    if url == "edit":
        url = edit_url(add_tool(mock_app, alice_id))

    html = logged_in_client.get(url).get_data(as_text=True)

    assert 'type="file" id="photo" name="photo"' in html
    assert 'enctype="multipart/form-data"' in html


def test_edit_form_offers_two_unticked_boxes(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")
    give_photo(mock_app, tool_id, jpeg_photo)

    html = page_text(logged_in_client.get(edit_url(tool_id)))

    assert f'src="{photo_url(tool_id)}" alt="perceuse"' in html
    assert REPLACE in html and REMOVAL_WARNING in html
    assert ADD not in html
    assert 'type="checkbox" id="photo-replace" name="replace_photo"' in html
    assert 'type="checkbox" id="photo-remove" name="remove_photo"' in html
    assert "checked" not in html


@pytest.mark.parametrize("url", ["/tools/new", "edit"])
def test_forms_without_photo_only_offer_to_add_one(mock_app, logged_in_client, alice_id, url):
    if url == "edit":
        url = edit_url(add_tool(mock_app, alice_id))

    html = page_text(logged_in_client.get(url))

    assert ADD in html
    assert 'class="tool-photo"' not in html
    assert REPLACE not in html and REMOVE not in html


def test_tool_is_created_with_its_photo(mock_app, logged_in_client, alice_id, jpeg_photo):
    response = post_form(logged_in_client, "/tools/new", with_file(jpeg_photo))

    assert response.status_code == 302
    with mock_app.app_context():
        tool = Tool.query.one()
        assert photos.load_photo(tool).content_type == "image/jpeg"


def test_tool_is_created_without_a_file(mock_app, logged_in_client, alice_id):
    post_form(logged_in_client, "/tools/new", {**tool_form(), "photo": (BytesIO(b""), "")})

    with mock_app.app_context():
        assert photos.load_photo(Tool.query.one()) is None


def test_refused_photo_creates_no_tool(mock_app, logged_in_client, alice_id, gif_image):
    response = post_form(
        logged_in_client, "/tools/new", with_file(gif_image, "scie.gif", name="scie")
    )

    html = page_text(response)
    assert tool_count(mock_app) == 0
    assert 'value="scie"' in html
    assert photos.WRONG_FORMAT in html
    assert "Choisissez de nouveau la photo" in html


def test_png_photo_is_added_when_editing(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    response = post_form(
        logged_in_client, edit_url(tool_id), with_file(encoded(a_photo(), "PNG"), "x.png")
    )

    assert response.status_code == 302
    assert photo_of(mock_app, tool_id) is not None


def another_photo():
    return encoded(a_photo((640, 480)), "PNG")


def test_photo_is_replaced_with_modifier(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    edit_with_photo(
        logged_in_client,
        tool_id,
        {**with_file(another_photo(), "x.png"), "replace_photo": "1"},
    )

    after = photo_of(mock_app, tool_id)
    assert after is not None and after != before


def test_editing_without_a_file_keeps_the_photo(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    edit_with_photo(logged_in_client, tool_id, tool_form(description="Nouvelle description"))

    assert stored(mock_app, tool_id)["description"] == "Nouvelle description"
    assert photo_of(mock_app, tool_id) == before


def test_photo_is_removed_with_retirer(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    edit_with_photo(logged_in_client, tool_id, {**tool_form(), "remove_photo": "1"})

    assert photo_of(mock_app, tool_id) is None


def test_file_chosen_then_retirer_removes_and_ignores_the_file(
    mock_app, logged_in_client, alice_id, jpeg_photo
):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    response = edit_with_photo(
        logged_in_client,
        tool_id,
        {**with_file(another_photo(), "x.png"), "remove_photo": "1"},
    )

    assert response.status_code == 302
    assert photo_of(mock_app, tool_id) is None


def test_file_without_a_choice_is_ignored(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    response = edit_with_photo(logged_in_client, tool_id, with_file(another_photo(), "x.png"))

    assert response.status_code == 302
    assert photo_of(mock_app, tool_id) == before


def test_modifier_without_a_file_is_refused(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    response = edit_with_photo(
        logged_in_client,
        tool_id,
        {**tool_form(name="foreuse"), "replace_photo": "1"},
    )

    html = page_text(response)
    assert "Choisissez la nouvelle image" in html
    assert re.search(r'name="replace_photo" value="1" checked', html)
    assert stored(mock_app, tool_id)["name"] == "perceuse"
    assert photo_of(mock_app, tool_id) == before


def test_change_of_mind_saves_the_rest_and_keeps_the_photo(
    mock_app, logged_in_client, alice_id, jpeg_photo
):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    response = edit_with_photo(
        logged_in_client,
        tool_id,
        with_file(another_photo(), "x.png", description="Nouvelle description"),
    )

    assert response.status_code == 302
    assert stored(mock_app, tool_id)["description"] == "Nouvelle description"
    assert photo_of(mock_app, tool_id) == before


def test_both_boxes_ticked_are_refused(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    response = edit_with_photo(
        logged_in_client,
        tool_id,
        {
            **with_file(another_photo(), "x.png", name="foreuse"),
            "replace_photo": "1",
            "remove_photo": "1",
        },
    )

    html = page_text(response)
    assert response.status_code == 200
    assert "Choisissez Modifier l'image ou Retirer l'image, pas les deux" in html
    assert stored(mock_app, tool_id)["name"] == "perceuse"
    assert photo_of(mock_app, tool_id) == before


def test_removing_an_already_removed_photo_succeeds(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    response = post_form(logged_in_client, edit_url(tool_id), {**tool_form(), "remove_photo": "1"})

    assert response.status_code == 302
    assert photo_of(mock_app, tool_id) is None


def test_refused_photo_leaves_the_tool_unchanged(
    mock_app, logged_in_client, alice_id, jpeg_photo, gif_image
):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    response = edit_with_photo(
        logged_in_client,
        tool_id,
        {**with_file(gif_image, "x.gif", name="foreuse"), "replace_photo": "1"},
    )

    html = page_text(response)
    assert stored(mock_app, tool_id)["name"] == "perceuse"
    assert photo_of(mock_app, tool_id) == before
    assert 'value="foreuse"' in html
    assert photos.WRONG_FORMAT in html


def test_photo_on_a_neighbours_tool_gets_404(mock_app, logged_in_client, bob_id, jpeg_photo):
    tool_id = add_tool(mock_app, bob_id)

    response = post_form(logged_in_client, edit_url(tool_id), with_file(jpeg_photo))

    assert response.status_code == 404
    assert photo_of(mock_app, tool_id) is None


def test_multipart_form_is_accepted_with_its_csrf_token(
    mock_app, csrf_client, alice_id, jpeg_photo
):
    log_in_with_page_token(csrf_client, "alice", USER_PASSWORD)
    tool_id = add_tool(mock_app, alice_id)
    token = token_in(csrf_client.get(edit_url(tool_id)))

    response = post_form(
        csrf_client, edit_url(tool_id), {**with_file(jpeg_photo), "csrf_token": token}
    )

    assert response.status_code == 302
    assert photo_of(mock_app, tool_id) is not None


def test_multipart_form_without_token_is_refused(mock_app, csrf_client, alice_id, jpeg_photo):
    log_in_with_page_token(csrf_client, "alice", USER_PASSWORD)
    tool_id = add_tool(mock_app, alice_id)

    response = post_form(csrf_client, edit_url(tool_id), with_file(jpeg_photo))

    assert response.status_code == 400
    assert photo_of(mock_app, tool_id) is None


def test_too_large_request_gets_a_french_413_page(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")
    mock_app.config["MAX_CONTENT_LENGTH"] = 1024

    response = post_form(
        logged_in_client, edit_url(tool_id), with_file(jpeg_photo + b"\0" * 2048, name="foreuse")
    )

    assert response.status_code == 413
    assert "Envoi trop volumineux" in page_text(response)
    assert "16 Mo" not in page_text(response)
    assert stored(mock_app, tool_id)["name"] == "perceuse"
    assert photo_of(mock_app, tool_id) is None


def test_requests_are_capped_at_16_mb(mock_app):
    assert mock_app.config["MAX_CONTENT_LENGTH"] == 16 * 1024 * 1024


def test_photo_over_10_mb_redisplays_the_form(mock_app, logged_in_client, alice_id):
    response = post_form(
        logged_in_client, "/tools/new", with_file(b"\0" * (11 * 1024 * 1024), name="scie")
    )

    html = page_text(response)
    assert response.status_code == 200
    assert photos.TOO_HEAVY in html
    assert 'value="scie"' in html
    assert tool_count(mock_app) == 0


def test_list_shows_a_thumbnail_named_after_the_tool(
    mock_app, logged_in_client, alice_id, jpeg_photo
):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")
    give_photo(mock_app, tool_id, jpeg_photo)

    html = page_text(logged_in_client.get("/tools/mine"))

    assert f'class="tool-thumb" src="{photo_url(tool_id)}" alt="perceuse"' in html


def test_list_shows_no_image_for_a_tool_without_photo(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, name="scie")

    html = page_text(logged_in_client.get("/tools/mine"))

    assert "scie" in html
    assert "<img" not in html
    assert photo_url(tool_id) not in html


def test_retired_list_shows_the_thumbnail(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id, name="perceuse", is_active=False)
    give_photo(mock_app, tool_id, jpeg_photo)

    html = page_text(logged_in_client.get("/tools/mine/retired"))

    assert f'class="tool-thumb" src="{photo_url(tool_id)}" alt="perceuse"' in html


@pytest.mark.parametrize(
    ("fixture", "filename", "message"),
    [
        ("gif_image", "x.gif", photos.WRONG_FORMAT),
        ("text_named_jpeg", "perceuse.jpg", photos.WRONG_FORMAT),
        ("truncated_jpeg", "x.jpg", photos.UNREADABLE),
        ("empty_file", "x.jpg", photos.UNREADABLE),
        ("huge_png", "x.png", photos.TOO_LARGE),
    ],
)
@pytest.mark.filterwarnings("ignore::PIL.Image.DecompressionBombWarning")
def test_form_shows_why_a_photo_is_refused(
    request, mock_app, logged_in_client, alice_id, fixture, filename, message
):
    data = request.getfixturevalue(fixture)

    response = post_form(logged_in_client, "/tools/new", with_file(data, filename, name="scie"))

    html = page_text(response)
    assert message in html
    assert 'value="scie"' in html
    assert tool_count(mock_app) == 0


@pytest.fixture
def text_named_jpeg():
    return b"Ceci n'est pas une image"


@pytest.fixture
def empty_file():
    return b""


def served_after_upload(mock_app, client, alice_id, data, filename="photo.jpg"):
    """The image the route serves once the owner has added this file to one of their tools"""
    tool_id = add_tool(mock_app, alice_id)
    post_form(client, edit_url(tool_id), with_file(data, filename))
    return opened(client.get(photo_url(tool_id)).get_data())


def test_served_photo_is_reduced(mock_app, logged_in_client, alice_id, large_geotagged_photo):
    image = served_after_upload(mock_app, logged_in_client, alice_id, large_geotagged_photo)

    assert (image.format, image.size) == ("JPEG", (1600, 1200))


def test_served_small_photo_keeps_its_size(mock_app, logged_in_client, alice_id):
    png = encoded(a_photo((800, 600)), "PNG")

    image = served_after_upload(mock_app, logged_in_client, alice_id, png, "x.png")

    assert (image.format, image.size) == ("JPEG", (800, 600))


def test_served_photo_has_no_metadata(mock_app, logged_in_client, alice_id, large_geotagged_photo):
    image = served_after_upload(mock_app, logged_in_client, alice_id, large_geotagged_photo)

    assert not image.getexif()


def test_served_photo_is_upright(mock_app, logged_in_client, alice_id, sideways_photo):
    image = served_after_upload(mock_app, logged_in_client, alice_id, sideways_photo)

    assert image.size == (1200, 1600)


def test_too_long_text_gets_the_same_generic_413_page(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id, name="perceuse")

    response = post_form(
        logged_in_client,
        edit_url(tool_id),
        {**tool_form(description="x" * 600_000), "photo": (BytesIO(b""), "")},
    )

    html = page_text(response)
    assert response.status_code == 413
    assert "Envoi trop volumineux" in html
    assert "16 Mo" not in html
    assert stored(mock_app, tool_id)["name"] == "perceuse"


def test_stale_tab_retirer_with_a_file_saves_no_photo(mock_app, logged_in_client, alice_id):
    """The photo was removed in another tab; this one still shows the boxes"""
    tool_id = add_tool(mock_app, alice_id)

    response = edit_with_photo(
        logged_in_client, tool_id, {**with_file(another_photo(), "x.png"), "remove_photo": "1"}
    )

    assert response.status_code == 302
    assert photo_of(mock_app, tool_id) is None


def test_stale_tab_both_boxes_are_refused(mock_app, logged_in_client, alice_id):
    tool_id = add_tool(mock_app, alice_id)

    response = edit_with_photo(
        logged_in_client,
        tool_id,
        {**with_file(another_photo(), "x.png"), "replace_photo": "1", "remove_photo": "1"},
    )

    assert "Choisissez Modifier l'image ou Retirer l'image, pas les deux" in page_text(response)
    assert photo_of(mock_app, tool_id) is None


def test_file_from_a_form_opened_without_photo_does_not_replace_a_newer_one(
    mock_app, logged_in_client, alice_id, jpeg_photo
):
    """The form showed "Ajouter une image"; another tab has given the tool a photo since"""
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)
    before = photo_of(mock_app, tool_id)

    response = post_form(logged_in_client, edit_url(tool_id), with_file(another_photo(), "x.png"))

    html = page_text(response)
    assert "Choisissez la nouvelle image" in html
    assert REPLACE in html
    assert photo_of(mock_app, tool_id) == before


def test_new_image_field_has_an_accessible_name(mock_app, logged_in_client, alice_id, jpeg_photo):
    tool_id = add_tool(mock_app, alice_id)
    give_photo(mock_app, tool_id, jpeg_photo)

    html = page_text(logged_in_client.get(edit_url(tool_id)))

    assert 'aria-label="Nouvelle image"' in html
    assert '<input type="hidden" name="had_photo" value="1">' in html
