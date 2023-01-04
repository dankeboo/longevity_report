curl -u admin:Chang3d! -k https://10.224.18.195:8089/services/search/jobs -d search='search index=_introspection sourcetype=splunk_resource_usage component=Hostwide host=sh* | rename data.* as *| eval cpu=cpu_system_pct%2Bcpu_user_pct | timechart minspan=10s  avg(cpu) as cpu_usage by host limit=0'

 curl -u admin:Chang3d! -k https://10.224.18.195:8089/services/search/jobs/1672794277.1023

 curl -u admin:Chang3d! -k https://10.224.18.195:8089/services/search/jobs/1672794714.1084/results/ --get -d output_mode=csv

