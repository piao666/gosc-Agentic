"""Observe original Ollama transport without changing inference options or retries."""
import hashlib
import json
import time

class ObservedTransport:
    def __init__(self,send,path):self.send=send;self.path=path;self.events=[];self.context={}
    def __call__(self,body):
        start=time.monotonic();row={**self.context,'model':body['model'],'prompt_sha256':hashlib.sha256(body['prompt'].encode()).hexdigest(),'options':body.get('options'),'status':'http_started'}
        try:
            response=self.send(body)
            for k in ['prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration','done','done_reason']:row[k]=response.get(k)
            try:
                value=json.loads(response['response']);choice=value.get('choice');allowed=body.get('format',{}).get('properties',{}).get('choice',{}).get('enum',[])
                row['format_valid']=choice in allowed;row['choice']=choice
            except (ValueError,KeyError,TypeError,AttributeError):row['format_valid']=False
            row['status']='http_returned';return response
        except BaseException as e:row.update(status='http_failed',error=repr(e));raise
        finally:
            row['wall_seconds']=time.monotonic()-start;self.events.append(row)
            with self.path.open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
