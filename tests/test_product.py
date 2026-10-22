import unittest, tempfile, os
import app
from unittest.mock import MagicMock, patch
import json

class ProductTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.NamedTemporaryFile(delete=False); self.tmp.close(); app.DB=__import__('pathlib').Path(self.tmp.name); app.init_db()
    def tearDown(self): os.unlink(self.tmp.name)
    def test_score_is_deterministic_and_bounded(self):
        with app.connect() as d: a=d.execute('select * from companies where id=1').fetchone(); b=d.execute('select * from companies where id=2').fetchone()
        one=app.score(a,b,'partnership'); self.assertEqual(one,app.score(a,b,'partnership')); self.assertGreaterEqual(one[0],0); self.assertLessEqual(one[0],100)
    def test_equity_data_gap_is_visible_in_rubric(self):
        with app.connect() as d: a=d.execute('select * from companies where id=1').fetchone(); b=d.execute('select * from companies where id=2').fetchone()
        value,parts=app.score(a,b,'investment'); self.assertEqual(parts[1][1],0); self.assertLess(value,70)
    def test_kpi_directions(self):
        self.assertEqual(app.achievement(100,65,'higher'),65.0)
        self.assertEqual(app.achievement(100,125,'lower'),80.0)
    def test_event_telemetry_persists(self):
        app.record('test','failure',12,'example')
        with app.connect() as d: self.assertEqual(d.execute('select count(*) from events').fetchone()[0],1)
    def test_gemini_json_api_integration(self):
        answer={'summary':'Evidence-based interpretation.','opportunities':['Explore a pilot.'],'risks':['Demand is unverified.'],'evidence':['Company description A','Company description B']}
        response=MagicMock(); response.__enter__.return_value.read.return_value=json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(answer)}]}}]}).encode()
        a={'name':'A','ticker':'A1','description':'Description A','products':'A products','sector':'A','revenue':None}
        b={'name':'B','ticker':'B1','description':'Description B','products':'B products','sector':'B','revenue':None}
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'gemini-test','OPENAI_API_KEY':''},clear=True), patch('app.urllib.request.urlopen',return_value=response) as call:
            result=app.ai_explain(a,b,'partnership',[('sector',82,.55)])
        self.assertEqual(result['mode'],'Gemini API')
        self.assertEqual(result['result'],answer)
        request=call.call_args.args[0]
        self.assertIn('/models/gemini-test:generateContent',request.full_url)
        self.assertEqual(request.get_header('X-goog-api-key'),'test-key')

if __name__=='__main__': unittest.main()
