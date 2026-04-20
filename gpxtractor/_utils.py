import pathlib
import gzip


def _get_file_extensions(file_path: pathlib.Path) -> str:
    path = pathlib.Path(file_path)
    return "".join(path.suffixes)


def _get_file_type_from_extensions(extensions) -> str:
    match extensions:
        case ".gpx" | ".gpx.gz":
            return "GPX"
        case ".tcx" | ".tcx.gz":
            return "TCX"
        case ".fit" | ".fit.gz":
            return "FIT"


def _handle_gzipped_xml_files(
    file_path: pathlib.Path, extensions, sport_func, extraction_func
):
    is_gzipped = ".gz" in extensions
    if is_gzipped:
        with gzip.open(file_path, "rt") as gz:
            sport = sport_func(gz)
        with gzip.GzipFile(file_path, "r") as gz:
            return sport, extraction_func(gz)
    else:
        with open(file_path, "r") as file:
            sport = sport_func(file)
        return sport, extraction_func(file_path)
