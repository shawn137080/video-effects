import hashlib,importlib.util,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('release_tools',ROOT/'tools/release.py');release=importlib.util.module_from_spec(s);s.loader.exec_module(release)
class DistributionTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
 def tearDown(self):self.t.cleanup()
 def package(self):
  p=self.root/'package';(p/'video-effects').mkdir(parents=True);shutil.copy2(ROOT/'install.py',p/'install.py');entry=p/'video-effects/SKILL.md';entry.write_text('Verified skill');(p/'video-effects/private.txt').write_text('must not install')
  (p/'MANIFEST.json').write_text(json.dumps({'files':{'video-effects/SKILL.md':hashlib.sha256(entry.read_bytes()).hexdigest()}}));return p
 def install(self,p,extra=None):return subprocess.run([sys.executable,str(p/'install.py'),'--agent','codex','--root',str(self.root/'skills'),*(extra or [])],capture_output=True,text=True)
 def test_only_manifest_payload_installs(self):
  p=self.package();r=self.install(p);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse((self.root/'skills/video-effects/private.txt').exists())
 def test_upgrade_keeps_user_runtime_and_full_backup(self):
  p=self.package();self.assertEqual(self.install(p).returncode,0);dest=self.root/'skills/video-effects';(dest/'custom.txt').write_text('custom');(dest/'runtime.local.json').write_text('{"gsap":"local"}')
  self.assertNotEqual(self.install(p).returncode,0);r=self.install(p,['--upgrade']);self.assertEqual(r.returncode,0,r.stderr);receipt=json.loads(r.stdout);self.assertTrue((Path(receipt['backup'])/'custom.txt').exists());self.assertEqual(json.loads((dest/'runtime.local.json').read_text())['gsap'],'local')
 def test_modified_payload_fails_before_install(self):
  p=self.package();(p/'video-effects/SKILL.md').write_text('tampered');self.assertNotEqual(self.install(p).returncode,0);self.assertFalse((self.root/'skills').exists())
 def test_manifest_traversal_blocked(self):
  p=self.package();(p/'MANIFEST.json').write_text(json.dumps({'files':{'../escape':'0'}}));self.assertNotEqual(self.install(p).returncode,0)
 def test_private_runtime_is_never_archived(self):
  (self.root/'video-effects').mkdir();(self.root/'video-effects/runtime.local.json').write_text('{}')
  with self.assertRaisesRegex(ValueError,'Private'):release.files(self.root)
 def test_media_is_not_accepted_inside_skill(self):
  (self.root/'video-effects').mkdir();(self.root/'video-effects/take.mp4').write_bytes(b'private')
  with self.assertRaisesRegex(ValueError,'Unallowlisted'):release.files(self.root)
 def test_nested_symlink_rejected(self):
  (self.root/'video-effects').mkdir();(self.root/'outside.txt').write_text('private');(self.root/'video-effects/linked.txt').symlink_to(self.root/'outside.txt')
  with self.assertRaises(ValueError):release.files(self.root)
if __name__=='__main__':unittest.main()
