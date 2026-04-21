import os
import pytest


asset_dir = "assets"
rides_dir = os.path.join(asset_dir, "rides")
runs_dir = os.path.join(asset_dir, "runs")


def _generate_filepaths_from_dir(dir):
    for file in os.listdir(dir):
        yield os.path.join(dir, file)


def _generate_all_asset_filepaths():
    for root, dirs, files in os.walk("assets"):
        for file in files:
            yield os.path.join(root, file)


def _generate_filepaths_filtered(file_extension):
    for filepath in _generate_all_asset_filepaths():
        if filepath.endswith(file_extension):
            yield filepath


@pytest.fixture
def all_filepaths():
    return _generate_all_asset_filepaths()


@pytest.fixture
def gpx_filepaths():
    return _generate_filepaths_filtered(".gpx")


@pytest.fixture
def tcx_filepaths():
    return _generate_filepaths_filtered(".tcx")


@pytest.fixture
def fit_filepaths():
    return _generate_filepaths_filtered(".fit")


@pytest.fixture
def run_filepaths():
    return _generate_filepaths_from_dir(runs_dir)


@pytest.fixture
def ride_filepaths():
    return _generate_filepaths_from_dir(rides_dir)
