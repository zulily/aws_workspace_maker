#!/usr/bin/env python
"""
   Tests for common_utils.py
   Called via nosetests test_common_utils.py
"""

# Global imports
import unittest

# Local imports
import common_utils
import workspacer


class TestCommonUtils(unittest.TestCase):
    """
    Standard test class, for all common_utils functions
    """

    def test_load_config_json(self):
        """
        Test the method used for loading the config json
        Note if any config files diverge, a separate test should be added
        """
        config_info = common_utils.load_config_json(workspacer.CONFIG_FILE)
        self.assertEqual(len(config_info), 10)
        self.assertGreaterEqual(len(config_info['secret_info']), 3)


    def test_determine_team_bundle_id(self):
        """
        Test the method that returns the correct bundle_id
        """
        test_bundles = {'image_win10_power_20210801_test': {'BundleId': 'abc-123123123'},
                        'image_win10_power_20210803_test': {'BundleId': 'abc-123123124'},
                        'image_win10_power_20210805_testlatest': {'BundleId': 'abc-123123126'},
                        'image_win10_power_20210805': {'BundleId': 'abc-123123125'},
                        'image_win10_power_20210705': {'BundleId': 'abc-123123120'}}
        bundle_id = common_utils.determine_team_bundle_id(test_bundles, 'test')
        self.assertEqual(bundle_id, 'abc-123123124')
        bundle_id = common_utils.determine_team_bundle_id(test_bundles, 'testlatest')
        self.assertEqual(bundle_id, 'abc-123123126')
        bundle_id = common_utils.determine_team_bundle_id(test_bundles, 'notest')
        self.assertEqual(bundle_id, 'abc-123123125')
        test_bundles = { 'image_win10_power_20210805_testlatest': {'BundleId': 'abc-123123126'}}
        bundle_id = common_utils.determine_team_bundle_id(test_bundles, 'notest')
        self.assertEqual(bundle_id, None)

if __name__ == '__main__':
    unittest.main()
