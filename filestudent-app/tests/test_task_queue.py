from filestudent.core.task_queue import TaskQueue


def test_submit_success_relays_result(qapp, pump):
    queue = TaskQueue()
    results: list[int] = []
    errors: list[str] = []

    queue.submit(lambda x: x * 2, 21, on_finished=results.append, on_error=errors.append)
    queue.wait_for_done(5000)
    pump()

    assert results == [42]
    assert errors == []


def test_submit_error_is_caught_not_raised(qapp, pump):
    queue = TaskQueue()
    results: list[object] = []
    errors: list[str] = []

    def boom() -> None:
        raise ValueError("module pas encore implemente")

    queue.submit(boom, on_finished=results.append, on_error=errors.append)
    queue.wait_for_done(5000)
    pump()

    assert results == []
    assert len(errors) == 1
    assert "module pas encore implemente" in errors[0]


def test_real_module_runs_through_the_queue(qapp, pump, tmp_path):
    """Un vrai module (pas un stub) execute par la file de traitement, pour
    verifier que le resultat est bien relaye jusqu'a l'appelant."""
    from PIL import Image

    from filestudent.modules import conversion

    img_path = tmp_path / "photo.png"
    Image.new("RGB", (10, 10), (0, 0, 0)).save(img_path)

    results: list[object] = []
    errors: list[str] = []
    queue = TaskQueue()
    queue.submit(
        conversion.run, [str(img_path)], target="PDF", on_finished=results.append,
        on_error=errors.append,
    )
    queue.wait_for_done(5000)
    pump()

    assert errors == []
    assert len(results) == 1
    assert (tmp_path / "photo.pdf").exists()
