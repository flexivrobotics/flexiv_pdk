"""Reading a license or identifier file into what the gRPC field expects.

Flexiv issues a license as a `.lic` file holding the raw license bundle, and
prints the same bytes as base64 between two markers. `SaveRequest.license` is
the base64 form: the server decodes it and writes the bytes into its license
folder. Encoding the file is therefore part of installing it, and the rule lives
here so the CLI, the examples and client code do not each carry a copy.
"""
import base64
import pathlib
import string

# A raw bundle is protobuf, so it carries bytes outside the base64 alphabet.
# That is what tells the two forms of the file apart.
_BASE64_CHARACTERS = frozenset(string.ascii_letters + string.digits + "+/=")

# What the server accepts as a file name: a plain name, no directories.
_SAFE_FILE_CHARACTERS = frozenset(string.ascii_letters + string.digits + "-_.")


def license_text(raw: bytes) -> str:
    """Return the base64 for ``SaveRequest.license``, from either form of file.

    Args:
      raw: The bytes of a `.lic` file, or of a file holding its base64 text.
        Whitespace in the base64 form is ignored, so a line-wrapped file works.

    Returns:
      Base64 text, ready to send. Already-encoded input is passed through
      rather than encoded twice.
    """
    compact = bytes(byte for byte in raw if byte not in b" \t\r\n")
    if compact and all(chr(byte) in _BASE64_CHARACTERS for byte in compact):
        return compact.decode("ascii")
    return base64.b64encode(raw).decode("ascii")


def read_license_file(path) -> str:
    """Read a license file and return the base64 for ``SaveRequest.license``.

    Args:
      path: Path to the `.lic` file Flexiv sent.

    Returns:
      Base64 text, ready to send.

    Raises:
      OSError: The file cannot be read.
      ValueError: The file is empty.
    """
    raw = pathlib.Path(path).read_bytes()
    if not raw.strip():
        raise ValueError(f"{path} is empty. Ask Flexiv to send it again.")
    return license_text(raw)


def server_file_name(path) -> str:
    """Return the name the server should save the license as, or "" to let it choose.

    Keeping Flexiv's own file name is what lets a support question be answered
    against `issued_licenses.log` months later. The server requires a plain
    name, so a file called "acme licence (1).lic" cannot keep its own.

    Args:
      path: Path to the `.lic` file Flexiv sent.

    Returns:
      The file's own name if the server will accept it, otherwise "", which
      makes the server name the file after the license id.
    """
    name = pathlib.Path(path).name
    if name and all(character in _SAFE_FILE_CHARACTERS for character in name):
        return name
    return ""
