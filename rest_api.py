import requests
import xml.etree.ElementTree as ET
import time

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

data = 'search=search index=_introspection sourcetype=splunk_resource_usage component=Hostwide host=sh* | rename data.* as *| eval cpu=cpu_system_pct%2Bcpu_user_pct | timechart minspan=10s  avg(cpu) as cpu_usage by host limit=0'

response = requests.post(
    'https://10.224.18.195:8089/services/search/jobs',
    headers=headers,
    data=data,
    verify=False,
    auth=('admin', 'Chang3d!'),
)

root = ET.fromstring(response.text)
sid = root[0].text

time.sleep(5)

params = {
    'output_mode': 'csv',
}

response = requests.get(
    'https://10.224.18.195:8089/services/search/jobs/{}/results/'.format(sid),
    params=params,
    verify=False,
    auth=('admin', 'Chang3d!'),
)

print(response.text)
