import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import collect_demand

class CollectorTests(unittest.TestCase):
    def test_failed_refresh_retains_original_data_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'output.json';old={'asOf':'2026-09-01T00:00:00+00:00','orders':[]}
            out.write_text(json.dumps({'ok':True,'data':old}))
            argv=['collector','--raw-dir',tmp,'--out',str(out),'--ecom-bin','ecom','--ecom-config','ecom.toml','--oms-bin','oms','--oms-config','oms.toml']
            with patch('sys.argv',argv),patch.object(collect_demand,'renew_auth',side_effect=RuntimeError('fixture failure')),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(collect_demand.main(),1)
            result=json.loads(out.read_text());self.assertFalse(result['ok']);self.assertEqual(result['data'],old);self.assertEqual(result['asOf'],old['asOf']);self.assertNotEqual(result['attemptedAt'],old['asOf'])
    def test_planner_reference_preserves_source_clock_and_plan_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'planner.json';stamp='2026-09-01T00:00:00+00:00'
            p.write_text(json.dumps({'meta':{'state_collected_at':stamp},'items':{'FG1':{'name':'wrong generic label'}},'plan':[{'code':'FG1','sku':'correct plan label','litres_per_piece':1}]}))
            collect_demand.refresh_planner_identity(SimpleNamespace(planner_inputs=str(p),raw_dir=tmp))
            result=json.loads((root/'planner-identity.json').read_text());self.assertEqual(result['asOf'],stamp);self.assertEqual(result['items']['FG1'],{'name':'correct plan label','packLitres':1})
    def test_inherited_tokens_cannot_override_isolated_config(self):
        with patch.dict('os.environ',{'OMS_TOKEN':'unrelated','JIVO_ECOM_TOKEN':'unrelated'}),patch.object(collect_demand.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{}',stderr='')) as run:
            collect_demand.cli('fixture',['orders'],'isolated.toml')
            env=run.call_args.kwargs['env'];self.assertNotIn('OMS_TOKEN',env);self.assertNotIn('JIVO_ECOM_TOKEN',env)
if __name__=='__main__':unittest.main()
