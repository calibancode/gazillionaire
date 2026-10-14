"""Regression checks for source-shape recovery; no game installation required."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clean_source import (clean_codegen, clean_control_flow, clean_members,
                          clean_planet_chains, method_span)
from assignment_manifest import generate


def method(name, body, role=""):
    return "      public function " + role + name + "() : void\n      {\n" + body + "\n      }\n"


class SourceCleanupChecks(unittest.TestCase):
    def test_manifest_generation_and_count_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, rebuilt, sources = (root / name for name in ('original', 'rebuilt', 'sources'))
            for path in (original, rebuilt, sources):
                path.mkdir()
            identity = 'CustomPreloader/instance/1:mn7(19:SWFDownloadCompleteprivate:15:CustomPreloader)'
            for path, digest, opcode in ((original, 'a', 'initproperty'), (rebuilt, 'b', 'setproperty')):
                (path / 'inventory.tsv').write_text('identity\tsha256\tscope\n'
                                                  + identity + '\t' + digest + '\tgenerated\n')
                (path / (digest + '.txt')).write_text(identity + '\n' + opcode + ' 18:mn7(6:_timer22:0:)\n')
            source = method('SWFDownloadComplete', '         this._timer = new Timer(1);')
            (sources / 'CustomPreloader.as').write_text(source)
            self.assertEqual(generate(original, rebuilt, sources),
                             {'CustomPreloader.as': {'SWFDownloadComplete': {'_timer': 1}}})
            (sources / 'CustomPreloader.as').write_text(source.replace('this._timer =', 'other ='))
            with self.assertRaisesRegex(ValueError, 'assignment count mismatch'):
                generate(original, rebuilt, sources)

    def test_implicit_write_keeps_reads_and_other_methods(self):
        source = method("SWFDownloadComplete", "         this._timer = new Timer(1);\n"
                        "         this._timer.start();")
        other = method("other", "         this._timer = null;")
        result = clean_members("CustomPreloader.as", source + other)
        self.assertIn("         _timer = new Timer(1);", result)
        self.assertIn("this._timer.start();", result)
        self.assertTrue(result.endswith(other))

    def test_member_count_drift_fails(self):
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            clean_members("CustomPreloader.as", method("SWFDownloadComplete", ""))

    def test_accessor_span(self):
        source = method("preloadedRSLs", "         return this._preloadedRSLs;", "get ")
        start, end = method_span(source, "preloadedRSLs")
        self.assertEqual(source[start:end], source.rstrip())
        with self.assertRaisesRegex(ValueError, "expected one method"):
            method_span(source + source, "preloadedRSLs")

    def test_resource_preserves_literal_order_and_return_local(self):
        source = method("getContent", '         return {"second":"B","first":"A"};')
        result = clean_codegen("en_US$effects_properties.as", source)
        self.assertIn('var content:Object = {"second":"B","first":"A"};', result)
        self.assertIn("return content;", result)

    def test_control_flow_is_scoped_and_counted(self):
        comparison = "         if(this.g.p[this.g.player].insurancePriceRange >= 6) {}"
        special = method("frm_Special_action", comparison + "\n" + comparison)
        def events(name, marker, count):
            branches = "\n".join("            if(test())\n            {\n"
                                 "               return true;\n            }" for _ in range(count))
            return method(name, "         " + marker + "\n         {\n"
                          + branches + "\n         }")
        good = events("frm_Travel2_goodEvent", "if(this.frame_globals[1] < 43)", 5)
        bad = events("frm_Travel2_badEvent", "if(this.frame_globals[1] > -12)", 7)
        commodity = method("commodity_sound", "         if(param1 == 0) {}\n"
                           "         if(param1 == 1) {}\n"
                           "         if(param2 == 0) {}\n         return 0;")
        result = clean_control_flow(special + good + bad + commodity + planet())
        self.assertEqual(result.count("if((this.g.p[this.g.player].insurancePriceRange >= 6))"), 2)
        self.assertEqual(result.count("            else if(test())"), 10)
        self.assertIn("else if(param1 == 1)", result)
        self.assertIn("         else\n         {\n            if(param2 == 0)", result)
        # planet_image_swf becomes two else-if chains with a shared else branch
        self.assertEqual(result.count("            else if(param1 == 1)"), 2)
        self.assertEqual(result.count("            else if(param1 == 12)"), 2)
        self.assertEqual(result.count("            else\n            {\n"
                                     "               return new this.PlanetNosh1Class()"), 2)
        with self.assertRaisesRegex(ValueError, "insurance comparisons"):
            clean_control_flow((special + good + bad + commodity + planet())
                               .replace(comparison, "", 1))

    def test_planet_chain_counts_are_checked(self):
        with self.assertRaisesRegex(ValueError, "planet selector count"):
            clean_planet_chains(planet(selectors=12))
        with self.assertRaisesRegex(ValueError, "planet selector statement"):
            clean_planet_chains(planet(fallback="return this.g.planetIndex;"))


def planet(selectors=13, fallback="return new this.PlanetNosh1Class() as MovieClip;"):
    """The flat, decompiled shape of planet_image_swf."""
    def chain(indent):
        branches = "".join(f"{indent}if(param1 == {index})\n{indent}{{\n"
                          f"{indent}   return new this.PlanetX{index}Class() as MovieClip;\n"
                          f"{indent}}}\n" for index in range(selectors))
        return branches + f"{indent}{fallback}\n"
    return ("      internal function planet_image_swf(param1:int, param2:int) : MovieClip\n"
            "      {\n"
            "         if(param2 == 1)\n"
            "         {\n" + chain("            ") + "         }\n"
            + chain("         ") + "      }\n")
