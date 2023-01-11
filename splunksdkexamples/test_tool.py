from search import main as search

bucket_span='3h'
es_sh='sh1'

spl_string = f"""search index=_introspection  sourcetype=splunk_resource_usage component=Hostwide host=i* 
    | rename data.* as * |eval cpu=cpu_system_pct+cpu_user_pct | bucket span={bucket_span} _time
    | stats  avg(cpu) as idx_cpu_usage , avg(mem_used) as idx_avg_mem_usage by _time  
    | eval idx_avg_mem_usage=round(idx_avg_mem_usage,0) | eval idx_cpu_usage=round(idx_cpu_usage,1)
    | appendcols [|search index=_introspection  sourcetype=splunk_resource_usage component=Hostwide host=sh* host={es_sh}* 
    | rename data.* as * |eval cpu=cpu_system_pct + cpu_user_pct| bucket span={bucket_span} _time
    | stats  avg(cpu) as es_cpu_usage, avg(mem_used) as es_avg_mem_usage  by _time  
    | eval es_avg_mem_usage=round(es_avg_mem_usage,0) | eval es_cpu_usage=round(es_cpu_usage,1)]
    | appendcols [|search index=_introspection  sourcetype=splunk_resource_usage component=Hostwide host=sh* host!={es_sh}** 
    | rename data.* as * |eval cpu=cpu_system_pct + cpu_user_pct| bucket span={bucket_span} _time
    | stats  avg(cpu) as sh_cpu_usage, avg(mem_used) as sh_avg_mem_usage  by _time 
    | eval sh_avg_mem_usage=round(sh_avg_mem_usage,0) | eval sh_cpu_usage=round(sh_cpu_usage,1)] 
    |table _time, idx_cpu_usage, idx_avg_mem_usage, es_cpu_usage, es_avg_mem_usage, sh_cpu_usage, sh_avg_mem_usage"""

argv=[
    spl_string,
    '--output_mode=csv'
]

search(argv)