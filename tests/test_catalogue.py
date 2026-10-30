import pytest

from agent.catalogue import get_metric, load_catalogue


def test_catalogue_entries_have_model_and_grain():
    for name, metric in load_catalogue().items():
        assert metric["model"] and metric["grain"], name


def test_unknown_metric_is_rejected():
    with pytest.raises(KeyError):
        get_metric("revenue_made_up")
