import metricslib

# hint: use sft ssh tunnel to access port 8089 in cloud env
#  sft ssh -L 8089:localhost:8089 52.205.242.226
# 

span='5m'
timecmd = ''
build = 'ib-c11'
host_samples="""
    (
        host=sh-i-08d78ca895e0f82be*
        OR 
        host=sh-i-05c6f78a25760a5d4*
        OR 
        host=c0m1-i-0b25d7ecf8841a3b*
        OR
        host=idx-i-06b3d0c75e30d380*
    )
    """

df=metricslib.get_results(span, timecmd, host_samples)
df.assign(build=[build,] * len(df.index))
df.to_csv('/tmp/metrics.csv')