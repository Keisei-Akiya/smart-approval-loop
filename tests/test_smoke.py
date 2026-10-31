from smart_approval_loop import adapters, core


def test_package_and_layers_import() -> None:
    assert adapters is not None
    assert core is not None
