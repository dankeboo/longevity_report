import metricslib    

span='5m'
timecmd = ''
build = 'ib-c11'

df=metricslib.get_results(span, timecmd)
df.assign(build=[build,] * len(df.index))
df.to_csv('/tmp/metrics.csv')