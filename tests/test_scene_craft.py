"""Contracts that prevent silent substitution, unsafe timing and exposed scene edges."""
import copy,importlib.util,math
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'video-effects/scripts/scene_craft.py'
s=importlib.util.spec_from_file_location('scene_craft_test',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class SceneCraftTests(unittest.TestCase):
 def plan(self,n=4):
  return {'treatment':'scene-craft','header':'25 video effects','headerSub':'created with Codex','fps':30,'frames':90,'assets':{'raw':{'file':'raw.mp4','compiled_file':'assets/raw.mp4'}},'beats':[{'id':'a','effect':n,'frames':90,'start_frame':0,'end_frame':90,'picture':{'asset':'raw'},'design':{}}]}
 def test_missing_matte_does_not_fall_back_to_opaque_video(self):
  with self.assertRaisesRegex(ValueError,'matte'):m.validate(self.plan(3))
 def test_missing_secondary_does_not_reuse_talking_head(self):
  with self.assertRaisesRegex(ValueError,'secondary'):m.validate(self.plan(10))
 def test_unsourced_chart_cannot_invent_data(self):
  with self.assertRaisesRegex(ValueError,'finite data'):m.validate(self.plan(8))
 def test_freeze_requires_visible_in_range_anchor(self):
  p=self.plan(24);p['beats'][0]['design']={'freeze':'raw','freezeFrame':90}
  with self.assertRaisesRegex(ValueError,'Freeze anchor'):m.validate(p)
 def test_through_cannot_zoom_back_into_same_scene_as_fallback(self):
  p=self.plan(15);p['beats'][0]['design']={'secondary':'raw'}
  with self.assertRaisesRegex(ValueError,'next-scene'):m.validate(p)
 def test_long_hierarchy_text_rejected_before_layout(self):
  p=self.plan();p['header']='X'*50
  with self.assertRaisesRegex(ValueError,'short'):m.validate(p)
 def test_camera_is_seek_deterministic_and_covers_canvas(self):
  p=self.plan();p['beats'][0]['effect']=5;p['frames']=90
  a=m.motion_samples(p);self.assertEqual(a,m.motion_samples(copy.deepcopy(p)))
  self.assertGreater(max(f['x'] for f in a)-min(f['x'] for f in a),30)
  for f in a:
   c=math.cos(math.radians(f['rotation']));s=math.sin(math.radians(f['rotation']))
   for x,y in [(0,0),(1080,0),(1080,1920),(0,1920)]:
    dx=x-540-f['x'];dy=y-921.6-f['y'];sx=(dx*c+dy*s)/f['scale']+540;sy=(-dx*s+dy*c)/f['scale']+921.6
    self.assertTrue(-.01<=sx<=1080.01 and -.01<=sy<=1920.01,(f,sx,sy))
 def test_new_live_scene_consumes_supplied_source(self):
  p=self.plan();body,js=m.scene(p,p['beats'][0],1)
  self.assertIn('assets/raw.mp4',body);self.assertNotIn('preview-',body)
  self.assertIn('sc-header',body);self.assertIn('sc-lower',body)
 def test_chinese_copy_is_opt_in_and_keeps_scene_structure(self):
  p=self.plan(14);body,_=m.scene(p,p['beats'][0],1)
  self.assertIn('Liquid clarity.',body)
  p['locale']='zh-Hans';body,_=m.scene(p,p['beats'][0],1)
  self.assertIn('流动的光。',body);self.assertNotIn('Liquid clarity.',body)
  self.assertIn('fx-a-glass',body);self.assertIn('sc-header',body)
 def test_unknown_locale_fails_instead_of_silent_font_fallback(self):
  p=self.plan();p['locale']='unknown'
  with self.assertRaisesRegex(ValueError,'locale'):m.validate(p)
 def test_frame_zero_captions_have_explicit_visibility(self):
  p=self.plan(0);b=p['beats'][0];b['id']='intro';b['captions']=[{'text':'First','local_frame':0,'frames':30},{'text':'Later','local_frame':30,'frames':30}]
  body,_=m.scene(p,b,0)
  self.assertIn('style="opacity:1">First',body)
  self.assertIn('style="opacity:0">Later',body)
 def test_gesture_cues_reject_unknown_fractional_and_out_of_shot_values(self):
  for cues in ({'typo':10},{'snap1':90},{'snap1':2.5},{'snap1':True},{'snap1':-1}):
   p=self.plan();p['beats'][0]['design']['cueFrames']=cues
   with self.assertRaisesRegex(ValueError,'cueFrames'):m.validate(p)
 def test_snap_is_one_frame_at_authored_hand_cues(self):
  p=self.plan();b=p['beats'][0];b['design']={'cueFrames':{'snap1':16,'snap2':25},'motionFrames':[16,25]}
  m.validate(p);_,js=m.scene(p,b,1);snap=[x for x in js if "tl.set('#fx-a-base'" in x]
  self.assertEqual(len(snap),2)
  self.assertTrue(snap[0].endswith(',0.5333333333333333);'))
  self.assertTrue(snap[1].endswith(',0.8333333333333334);'))
  self.assertFalse(any('duration' in x for x in snap))
  default=m.motion_samples(self.plan());shifted=m.motion_samples(p)
  self.assertNotEqual(default[16],shifted[16])
  p['beats'][0]['design']['motionFrames']=[25,16]
  with self.assertRaisesRegex(ValueError,'motionFrames'):m.validate(p)
 def test_magazine_waits_for_authored_pose_not_fixed_early_frame(self):
  p=self.plan(13);b=p['beats'][0];b['design']={'freeze':'raw','cueFrames':{'cover':29}}
  m.validate(p);_,js=m.scene(p,b,1)
  hold=[s for s in js if "tl.set('#fx-a-cover-freeze'" in s and '"opacity": 1' in s]
  self.assertEqual(len(hold),1);self.assertTrue(hold[0].endswith(',0.9666666666666667);'))
 def test_source_following_zoom_requires_ordered_bounded_keys(self):
  p=self.plan();d=p['beats'][0]['design'];d.update(refinement='gesture-v3',zoomKeys=[{'frame':0,'scale':1},{'frame':18,'scale':1.72},{'frame':32,'scale':.94}])
  m.validate(p);_,js=m.scene(p,p['beats'][0],1)
  self.assertTrue(any('"scale": 0.94' in x for x in js))
  d['zoomKeys'][1]['frame']=92
  with self.assertRaisesRegex(ValueError,'zoomKeys'):m.validate(p)
 def test_timer_needs_per_frame_valid_measurements_and_shared_scene_anchor(self):
  p=self.plan(21);d=p['beats'][0]['design'];d.update(refinement='gesture-v3',timerTrack=[{'x':740,'y':1150}]*90)
  m.validate(p);body,js=m.scene(p,p['beats'][0],1)
  self.assertIn('timer-anchor',body);self.assertIn('translateY(-80px)',body)
  d['timerTrack']=d['timerTrack'][:-1]
  with self.assertRaisesRegex(ValueError,'timerTrack'):m.validate(p)
 def test_image_fragments_require_matching_source_still(self):
  p=self.plan(17);p['beats'][0]['design'].update(refinement='gesture-v3',matte='raw')
  with self.assertRaisesRegex(ValueError,'breakStill'):m.validate(p)
if __name__=='__main__':unittest.main()
