import unittest
from contextlib import nullcontext
from unittest.mock import patch
from backend.search import drain

class Result:
    def __init__(self,value): self.value=value
    def fetchall(self): return self.value
    def fetchone(self): return self.value

class Connection:
    def __init__(self): self.ack=[]
    def transaction(self): return nullcontext()
    def execute(self,sql,args=None):
        if 'SELECT * FROM records.search_outbox' in sql:
            return Result([{'inmate_id':str(i),'version':7} for i in range(3)])
        if 'SELECT i.id::text' in sql:
            return Result({'id':args[0],'first_name':'Synthetic','last_name':'Example','visible':args[0]!='2'})
        if 'DELETE FROM records.search_outbox' in sql: self.ack.append(args)
        return Result(None)

class SearchBatchTests(unittest.TestCase):
    def test_batch_public_records_and_ack_exact_versions(self):
        c=Connection()
        with patch('backend.search.call',return_value={'taskUid':1}) as call,patch('backend.search.wait'):
            drain(c)
        self.assertEqual(call.call_count,2)
        self.assertEqual(len(call.call_args_list[0].args[2]),2)
        self.assertEqual(call.call_args_list[1].args,('DELETE','/indexes/bookings/documents/2'))
        self.assertEqual(c.ack,[('0',7),('1',7),('2',7)])

    def test_index_failure_does_not_ack_events(self):
        c=Connection()
        with patch('backend.search.call',return_value={'taskUid':1}),patch('backend.search.wait',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError): drain(c)
        self.assertEqual(c.ack,[])

if __name__=='__main__': unittest.main()
