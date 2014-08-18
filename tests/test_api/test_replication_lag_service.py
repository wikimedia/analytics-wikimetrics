import unittest
from datetime import datetime, timedelta

from wikimetrics.api import ReplicationLagService
from wikimetrics.models import Page, Revision, MediawikiUser

from tests.fixtures import DatabaseTest, mediawiki_project, second_mediawiki_project


class ReplicationLagServiceTest(DatabaseTest):
    """Test case for the database replication lag detection service"""

    def _add_edit(self, hour_offset, name='foo', mw_session=None):
        """Add an edit at a given hour offset in the past"""
        if not mw_session:
            mw_session = self.mwSession

        self.helper_insert_editors(
            name=name,
            editor_count=1,
            revisions_per_editor=1,
            revision_timestamps=datetime.now() - timedelta(hours=hour_offset),
            revision_lengths=4711,
            mw_session=mw_session
        )

    def test_any_lagged_without_wiki(self):
        service = ReplicationLagService(mw_projects=[])

        self.assertFalse(service.is_any_lagged())

    def test_any_lagged_single_wiki_without_lag(self):
        self._add_edit(hour_offset=2)

        service = ReplicationLagService(mw_projects=[mediawiki_project])

        self.assertFalse(service.is_any_lagged())

    def test_any_lagged_single_wiki_without_lag_but_older_revisions(self):
        self._add_edit(hour_offset=4, name='foo')
        self._add_edit(hour_offset=2, name='bar')

        service = ReplicationLagService(mw_projects=[mediawiki_project])

        self.assertFalse(service.is_any_lagged())

    def test_any_lagged_single_wiki_with_lag(self):
        self._add_edit(hour_offset=4)

        service = ReplicationLagService(mw_projects=[mediawiki_project])

        self.assertTrue(service.is_any_lagged())

    def test_any_lagged_single_wiki_large_threshold_without_lag(self):
        self._add_edit(hour_offset=29)

        service = ReplicationLagService(
            mw_projects=[mediawiki_project],
            lag_threshold=timedelta(hours=30),
        )

        self.assertFalse(service.is_any_lagged())

    def test_any_lagged_single_wiki_large_threshold_with_lag(self):
        self._add_edit(hour_offset=31)

        service = ReplicationLagService(
            mw_projects=[mediawiki_project],
            lag_threshold=timedelta(hours=30),
        )

        self.assertTrue(service.is_any_lagged())

    def test_any_lagged_two_wikis_both_without_lag(self):
        # Setup of wiki
        self._add_edit(hour_offset=1, mw_session=self.mwSession)

        # Setup of wiki2
        self._add_edit(hour_offset=2, mw_session=self.mwSession2)

        service = ReplicationLagService(mw_projects=[
            mediawiki_project,
            second_mediawiki_project,
        ])

        self.assertFalse(service.is_any_lagged())

    def test_any_lagged_two_wikis_both_with_lag(self):
        # Setup of wiki
        self._add_edit(hour_offset=4, mw_session=self.mwSession)

        # Setup of wiki2
        self._add_edit(hour_offset=4, mw_session=self.mwSession2)

        service = ReplicationLagService(mw_projects=[
            mediawiki_project,
            second_mediawiki_project,
        ])

        self.assertTrue(service.is_any_lagged())

    def test_any_lagged_two_wikis_first_with_lag(self):
        # Setup of wiki
        self._add_edit(hour_offset=4, mw_session=self.mwSession)

        # Setup of wiki2
        self._add_edit(hour_offset=1, mw_session=self.mwSession2)

        service = ReplicationLagService(mw_projects=[
            mediawiki_project,
            second_mediawiki_project,
        ])

        self.assertTrue(service.is_any_lagged())

    def test_any_lagged_two_wikis_second_with_lag(self):
        # Setup of wiki
        self._add_edit(hour_offset=1, mw_session=self.mwSession)

        # Setup of wiki2
        self._add_edit(hour_offset=4, mw_session=self.mwSession2)

        service = ReplicationLagService(mw_projects=[
            mediawiki_project,
            second_mediawiki_project,
        ])

        self.assertTrue(service.is_any_lagged())
