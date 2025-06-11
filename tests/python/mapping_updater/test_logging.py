import logging

import pytest

from kotobuki.mapping_updater.log import log_remapped_concepts


def test_unmapped_concepts_log_is_sorted(caplog: pytest.LogCaptureFixture):
    new_mappings = {0: None, 99: None, 42: None, 5: None, 100: None}
    with caplog.at_level(logging.INFO):
        log_remapped_concepts(new_mappings)
    assert "The following concept_ids could not be remapped: [0, 5, 42, 99, 100]" in caplog.text
