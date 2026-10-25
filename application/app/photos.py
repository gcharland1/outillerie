"""The only code that knows how tool photos are checked, stored and read (ADR 0008, ADR 0014)."""

import os
import warnings
from io import BytesIO
from typing import NamedTuple

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select

from app.extensions import db
from models.tool import ToolPhoto

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_SIDE = 1600
JPEG_QUALITY = 85
ACCEPTED_FORMATS = ("JPEG", "PNG", "WEBP")
STORED_CONTENT_TYPE = "image/jpeg"

WRONG_FORMAT = "La photo doit être une image JPEG, PNG ou WebP"
UNREADABLE = "La photo est illisible"
TOO_HEAVY = "La photo ne doit pas dépasser 10 Mo"
TOO_LARGE = "La photo ne doit pas dépasser 40 millions de pixels"

Image.MAX_IMAGE_PIXELS = MAX_PIXELS
# normalize() refuses these images itself, with a message for the owner.
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)


class StoredPhoto(NamedTuple):
    content: bytes
    content_type: str


class PhotoRejected(Exception):
    """A submitted photo that cannot be kept; its message is shown to the owner"""


def normalize(file_storage):
    """The submitted photo as JPEG bytes, upright, at most MAX_SIDE wide, without metadata"""
    stream = file_storage.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size == 0:
        raise PhotoRejected(UNREADABLE)
    if size > MAX_BYTES:
        raise PhotoRejected(TOO_HEAVY)

    try:
        image = Image.open(stream, formats=ACCEPTED_FORMATS)
    except UnidentifiedImageError as error:
        raise PhotoRejected(WRONG_FORMAT) from error
    except Image.DecompressionBombError as error:
        raise PhotoRejected(TOO_LARGE) from error
    except (OSError, SyntaxError, ValueError) as error:
        raise PhotoRejected(UNREADABLE) from error
    if image.width * image.height > MAX_PIXELS:
        raise PhotoRejected(TOO_LARGE)

    try:
        image.load()
        image = ImageOps.exif_transpose(image)
        image = _on_white(image)
        image.thumbnail((MAX_SIDE, MAX_SIDE))
        output = BytesIO()
        image.save(output, "JPEG", quality=JPEG_QUALITY)
    except (OSError, SyntaxError, ValueError) as error:
        raise PhotoRejected(UNREADABLE) from error
    return output.getvalue()


def save_photo(tool, jpeg_bytes):
    """Gives the tool this photo, replacing any previous one; the caller commits"""
    tool.photo = ToolPhoto(content=jpeg_bytes, content_type=STORED_CONTENT_TYPE)


def remove_photo(tool):
    """Takes the tool's photo away, if it has one; the caller commits"""
    tool.photo = None


def load_photo(tool):
    """The tool's photo as served, or None; callers never see where it is stored"""
    if tool.photo is None:
        return None
    return StoredPhoto(tool.photo.content, tool.photo.content_type)


def tool_ids_with_photo(tool_ids):
    """Which of these tools have a photo, without reading any photo's content"""
    if not tool_ids:
        return set()
    return set(db.session.scalars(select(ToolPhoto.tool_id).where(ToolPhoto.tool_id.in_(tool_ids))))


def can_view_photo(user, tool):
    """Only the owner for now; a contact of the owner will be let in with the contacts' tool list"""
    return user.is_authenticated and tool.owner_id == user.id


def _on_white(image):
    """An RGB copy of the image, transparent areas laid on white since JPEG has no alpha"""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")
