"""Tests du module context_menu (ticket APP-23), sans machine Windows.

`winreg` n'existe que sous Windows : on le remplace par un faux module qui
simule un arbre de registre en memoire, pour verifier la logique reelle
d'installation/desinstallation (entrees directes, commandes) sans jamais
toucher un vrai registre.
"""

from __future__ import annotations

import pytest

from filestudent.core import context_menu


class FakeKeyHandle:
    def __init__(self, node: dict) -> None:
        self.node = node

    def __enter__(self) -> FakeKeyHandle:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class FakeWinReg:
    """Simule juste assez de l'API `winreg` pour tester context_menu.py."""

    HKEY_CURRENT_USER = object()
    REG_SZ = 1
    KEY_ALL_ACCESS = 0

    def __init__(self) -> None:
        self.root: dict = {"_values": {}, "_children": {}}

    def _navigate(self, path: str, create: bool) -> dict | None:
        node = self.root
        if not path:
            return node
        for part in path.split("\\"):
            children = node["_children"]
            if part not in children:
                if not create:
                    return None
                children[part] = {"_values": {}, "_children": {}}
            node = children[part]
        return node

    def CreateKey(self, _hkey, path: str) -> FakeKeyHandle:
        node = self._navigate(path, create=True)
        return FakeKeyHandle(node)

    def OpenKey(self, _hkey, path: str, *_args: object) -> FakeKeyHandle:
        node = self._navigate(path, create=False)
        if node is None:
            raise FileNotFoundError(path)
        return FakeKeyHandle(node)

    def SetValueEx(self, handle: FakeKeyHandle, name: str, _reserved, _type, value: str) -> None:
        handle.node["_values"][name] = value

    def QueryValueEx(self, handle: FakeKeyHandle, name: str) -> tuple[str, int]:
        if name not in handle.node["_values"]:
            raise FileNotFoundError(name)
        return handle.node["_values"][name], self.REG_SZ

    def DeleteKey(self, _hkey, path: str) -> None:
        *parent_parts, leaf = path.split("\\")
        parent = self._navigate("\\".join(parent_parts), create=False)
        if parent is None or leaf not in parent["_children"]:
            raise FileNotFoundError(path)
        del parent["_children"][leaf]

    def CloseKey(self, _handle: FakeKeyHandle) -> None:
        return None

    # --- aides de test, pas de l'API winreg reelle ---
    def default_value(self, path: str) -> str | None:
        node = self._navigate(path, create=False)
        return node["_values"].get("") if node else None

    def named_value(self, path: str, name: str) -> str | None:
        node = self._navigate(path, create=False)
        return node["_values"].get(name) if node else None

    def key_exists(self, path: str) -> bool:
        return self._navigate(path, create=False) is not None

    def delete_subkey(self, path: str) -> None:
        *parent_parts, leaf = path.split("\\")
        parent = self._navigate("\\".join(parent_parts), create=False)
        assert parent is not None
        del parent["_children"][leaf]


@pytest.fixture
def fake_registry(monkeypatch):
    fake = FakeWinReg()
    monkeypatch.setattr(context_menu, "is_windows", lambda: True)
    monkeypatch.setattr(context_menu, "_winreg", lambda: fake)
    return fake


def test_not_installed_by_default(fake_registry):
    assert context_menu.is_installed() is False


def test_install_creates_all_file_verbs_directly_no_cascade(fake_registry):
    problems = context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")

    assert problems == []
    assert context_menu.is_installed() is True

    for verb_id, label, _action in context_menu.FILE_VERBS:
        path = f"{context_menu.FILE_PARENT}\\{verb_id}"
        assert fake_registry.default_value(path) == label
        # Entree directe : la commande est juste en dessous, pas de cle
        # "shell" imbriquee (l'ancien mecanisme de sous-menu en cascade).
        assert fake_registry.default_value(f"{path}\\command")
        assert fake_registry.key_exists(f"{path}\\shell") is False


def test_watermark_command_is_correct(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")
    cmd = fake_registry.default_value(
        f"{context_menu.FILE_PARENT}\\FileStudent_Watermark\\command"
    )
    assert cmd == '"C:\\Apps\\FileStudent.exe" --action=watermark --file="%1"'


def test_open_command_still_passes_the_file(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")
    cmd = fake_registry.default_value(f"{context_menu.FILE_PARENT}\\FileStudent_Open\\command")
    assert cmd == '"C:\\Apps\\FileStudent.exe" --file="%1"'


def test_folder_archive_and_open_entries(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")

    archive_cmd = fake_registry.default_value(
        f"{context_menu.FOLDER_PARENT}\\FileStudent_Archive\\command"
    )
    assert archive_cmd == '"C:\\Apps\\FileStudent.exe" --action=archive --file="%1"'

    open_cmd = fake_registry.default_value(
        f"{context_menu.FOLDER_PARENT}\\FileStudent_OpenFolder\\command"
    )
    assert open_cmd == '"C:\\Apps\\FileStudent.exe"'


def test_background_entry(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")
    cmd = fake_registry.default_value(f"{context_menu.BACKGROUND_ROOT}\\command")
    assert cmd == '"C:\\Apps\\FileStudent.exe"'


def test_verify_reports_no_problems_after_a_clean_install(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")
    assert context_menu.verify() == []


def test_verify_reports_missing_command_after_partial_write(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")
    fake_registry.delete_subkey(f"{context_menu.FILE_PARENT}\\FileStudent_Watermark\\command")

    problems = context_menu.verify()
    assert any("filigrane" in p.lower() for p in problems)


def test_uninstall_removes_everything(fake_registry):
    context_menu.install(exe_path=r"C:\Apps\FileStudent.exe")
    assert context_menu.is_installed() is True

    context_menu.uninstall()

    assert context_menu.is_installed() is False
    for root in context_menu.ALL_ROOTS:
        assert fake_registry.key_exists(root) is False


def test_uninstall_when_nothing_installed_does_not_raise(fake_registry):
    context_menu.uninstall()  # ne doit pas lever d'exception
    assert context_menu.is_installed() is False


def test_reinstall_after_uninstall_works(fake_registry):
    context_menu.install(exe_path=r"C:\a\FileStudent.exe")
    context_menu.uninstall()
    context_menu.install(exe_path=r"C:\b\FileStudent.exe")
    assert context_menu.is_installed() is True
    cmd = fake_registry.default_value(f"{context_menu.FILE_PARENT}\\FileStudent_ToPDF\\command")
    assert "C:\\b\\FileStudent.exe" in cmd


def test_not_windows_reports_not_installed(monkeypatch):
    monkeypatch.setattr(context_menu, "is_windows", lambda: False)
    assert context_menu.is_installed() is False


def test_install_raises_clearly_off_windows(monkeypatch):
    monkeypatch.setattr(context_menu, "is_windows", lambda: False)
    with pytest.raises(RuntimeError, match="Windows"):
        context_menu.install()


def test_uninstall_is_a_no_op_off_windows(monkeypatch):
    monkeypatch.setattr(context_menu, "is_windows", lambda: False)
    context_menu.uninstall()  # ne doit pas lever d'exception
