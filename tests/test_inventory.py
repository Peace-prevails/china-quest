import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import asset_status as status

class InventoryTests(unittest.TestCase):
 def test_empty_inventory_and_dependency_blocks(self):
  with tempfile.TemporaryDirectory() as temp, patch.object(status,'ROOT',pathlib.Path(temp)):
   result=status.inventory()
   self.assertEqual(result['base_assets'],12)
   self.assertEqual(result['candidate_target_total'],22)
   self.assertEqual(result['approved_assets'],0)
   by_id={row['id']:row for row in result['assets']}
   self.assertTrue(by_id['CH01_OWNER']['ready_for_generation'])
   self.assertEqual(by_id['BG03_COUNTER']['blocked_by'],['BG02_SHOP_MAIN'])
   self.assertEqual(len(by_id['CG01_FILE_SLAM']['blocked_by']),3)
   output=pathlib.Path(temp)/'export.json'
   with self.assertRaises(ValueError):status.export_approved(output)
   self.assertFalse(output.exists())
