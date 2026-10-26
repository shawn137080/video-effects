import importlib.util,json,subprocess,tempfile,unittest,sys,os
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'video-effects/scripts'))
import effects
class AdapterTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);(self.root/'source.mp4').write_bytes(b'unit-test fixture')
  self.info={'format':{'duration':'10'},'streams':[{'codec_type':'video'}]}
 def tearDown(self):self.t.cleanup()
 def config(self):return {'effect':4,'inputFile':'source.mp4','duration':3.6}
 def test_requires_real_secondary_for_broll(self):
  c=self.config();c['effect']=10
  with patch.object(effects,'probe',return_value=self.info),self.assertRaisesRegex(ValueError,'secondary'):effects.preflight(c,self.root)
 def test_source_inpoint_is_normalized_once(self):
  c=self.config();c['startTime']=1.2
  with patch.object(effects,'probe',return_value=self.info):p,sources,_=effects.preflight(c,self.root)
  self.assertEqual(sources['raw'][1],36);self.assertEqual(p['beats'][0]['start_frame'],0)
 def test_short_source_rejected_before_output(self):
  c=self.config();c['startTime']=9
  with patch.object(effects,'probe',return_value=self.info),self.assertRaisesRegex(ValueError,'too short'):effects.preflight(c,self.root)
 def test_no_invented_chart(self):
  c=self.config();c['effect']=8
  with patch.object(effects,'probe',return_value=self.info),self.assertRaisesRegex(ValueError,'source'):effects.preflight(c,self.root)
 def test_through_requires_actual_next_source(self):
  c=self.config();c['effect']=15
  with patch.object(effects,'probe',return_value=self.info),self.assertRaises(KeyError):effects.preflight(c,self.root)
 def test_matched_matte_has_independent_trim_origin(self):
  c=self.config();c.update(effect=3,startTime=2,cutoutFile='source.mp4',cutoutStartTime=0)
  with patch.object(effects,'probe',return_value=self.info):p,s,_=effects.preflight(c,self.root)
  self.assertEqual(s['raw'][1],60);self.assertEqual(s['matte'][1],0)
 def test_freeze_is_extracted_at_selected_local_frame(self):
  c=self.config();c.update(effect=24,freezeFrame=37)
  with patch.object(effects,'probe',return_value=self.info):p,s,_=effects.preflight(c,self.root)
  self.assertEqual(p['beats'][0]['design']['freezeFrame'],37);self.assertNotIn('freeze',s)
 def test_title_and_color_injection_rejected_or_escaped(self):
  c=self.config();c['accentColor']='red;display:none'
  with self.assertRaisesRegex(ValueError,'accentColor'):effects.preflight(c,self.root)
 def test_stale_compile_blocks_render(self):
  p=self.root/'project';p.mkdir();(p/'index.html').write_text('initial')
  r={'schema':'video-effects/1','files':{'index.html':effects.digest(p/'index.html')},'compiler':{}}
  (p/'receipt.json').write_text(json.dumps(r));effects.verify(p);(p/'index.html').write_text('changed')
  with self.assertRaisesRegex(ValueError,'Stale'):effects.verify(p)
 def test_receipt_path_cannot_escape_project(self):
  (self.root/'receipt.json').write_text(json.dumps({'schema':'video-effects/1','files':{'../escape':'anything'},'compiler':{}}))
  with self.assertRaisesRegex(ValueError,'Unsafe'):effects.verify(self.root)
 def test_compiler_revisions_invalidate_receipts(self):
  (self.root/'receipt.json').write_text(json.dumps({'schema':'video-effects/1','files':{},'compiler':{'scene_craft.py':'stale'}}))
  with self.assertRaisesRegex(ValueError,'Compiler changed'):effects.verify(self.root)
 def test_magazine_freeze_cue_matches_selected_pose(self):
  c=self.config();c.update(effect=13,freezeFrame=37)
  with patch.object(effects,'probe',return_value=self.info):p,_,_=effects.preflight(c,self.root)
  self.assertEqual(p['beats'][0]['design']['cueFrames']['cover'],37)
 def test_headline_four_items_cannot_overrun_four_card_layout(self):
  c=self.config();c.update(effect=6,items=['one','two','three','four'])
  with patch.object(effects,'probe',return_value=self.info),self.assertRaisesRegex(ValueError,'items'):effects.preflight(c,self.root)
 def test_catalog_covers_exactly_25_templates(self):
  rows=json.loads((ROOT/'video-effects/catalog.json').read_text());self.assertEqual({r['id'] for r in rows},set(effects.scene_craft.FAMILIES));self.assertEqual(len(rows),25)
if __name__=='__main__':unittest.main()
