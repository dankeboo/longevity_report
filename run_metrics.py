import metricslib

# hint: use sft ssh tunnel to access port 8089 in cloud env
#  sft ssh -T -L 8189:localhost:8089 52.205.242.226
# 

span='5m'
timecmd = ''
build = 'ib-c11'

df=metricslib.get_results(span, timecmd)
df.assign(build=[build,] * len(df.index))
df.to_csv('/tmp/metrics.csv')