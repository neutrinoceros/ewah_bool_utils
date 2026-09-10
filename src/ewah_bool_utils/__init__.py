"""Top-level package for EWAH Bool Utils."""

from ewah_bool_utils.ewah_bool_wrap import *


def get_include() -> str:
    """
    Returns the directory that contains ewah*.h headers
    """
    from pathlib import Path

    # discover C headers dynamically
    # when installing from an sdist or in editable mode,
    # we expect them to be found at the original location (cpp)
    # In a wheel, however, they'll be in a directory defined in meson.build
    INSTALL_DIR = Path(__file__).parent
    candidate_paths: list[Path] = []
    for relpath in [("cpp",), ("..", "headers")]:
        if (p := INSTALL_DIR.joinpath(*relpath)).is_dir():
            candidate_paths.append(p.absolute())

    if not candidate_paths:
        raise FileNotFoundError

    if len(candidate_paths) > 1:
        raise FileExistsError

    return str(candidate_paths[0])
