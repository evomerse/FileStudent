import pytest

from filestudent.core.file_types import FileKind, detect_file_kind, label_for


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("cours.pdf", FileKind.PDF),
        ("photo.JPG", FileKind.IMAGE),
        ("archive.tar.gz", FileKind.ARCHIVE),
        ("notes.zip", FileKind.ARCHIVE),
        ("rapport.docx", FileKind.DOCUMENT),
        ("mystere.xyz", FileKind.UNKNOWN),
    ],
)
def test_detect_file_kind(name: str, expected: FileKind) -> None:
    assert detect_file_kind(name) == expected


def test_label_for_is_in_french() -> None:
    assert label_for(FileKind.PDF) == "PDF"
    assert label_for(FileKind.UNKNOWN) == "Inconnu"
