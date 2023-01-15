import os, io
import pandas as pd
from splunksdkexamples.search import main as search

def get_df_melt(d):
    argv=[
        d["spl"],
        '--output_mode=csv',
    ]
    print(f'processing scope: {d["scope"]}')
    try:
        results = search(argv)
        df = pd.read_csv(
            io.StringIO(results.read().decode('utf-8')),
            encoding='utf8',
            sep=',',
            low_memory=False
        )
    except Exception as e:
        print(f'something went wrong with scope: {d["scope"]} Exception: {e} was caught!!')
        return None
    else:
        df1 = df.melt(id_vars=['time', 'host', 'obj'])
        return df1.assign(scope=[d["scope"],] * len(df1.index))

def do_spl_list(span, optcmd):

    # PerProcess data is recorded every 10 seconds
    # Multipler to correct for aggregate (sum) span period
    switcher={
        "1d" : "*10/60/60/24",
        "1h" : "*10/60/60",
        "2h" : "*10/60/60/2",
        "3h" : "*10/60/60/3",
        "4h" : "*10/60/60/4",
        "6h" : "*10/60/60/6",
        "12h" : "*10/60/60/12",
        "10s" : "*10/10",
        "30s" : "*10/10/3",
        "1m" : "*10/60",
        "5m" : "*10/60/5",
        "10m" : "*10/60/10",
        "30m" : "*10/60/30",
    }

    # to get daily volume from span sum
    switcher2={
        "1d" : "*1",
        "1h" : "*24",
        "2h" : "*24/2",
        "3h" : "*24/3",
        "4h" : "*24/4",
        "6h" : "*24/6",
        "12h" : "*24/12",
        "10s" : "*60*60*24/10",
        "30s" : "*60*60*24/30",
        "1m" : "*60*24",
        "5m" : "*60*24/5",
        "10m" : "*60*24/10",
        "30m" : "*60*24/30",
    }

    # to get hourly volume from span sum
    switcher3={
        "1d" : "/24",
        "1h" : "*1",
        "2h" : "/2",
        "3h" : "/3",
        "4h" : "/4",
        "6h" : "/6",
        "12h" : "/12",
        "10s" : "*6*60",
        "30s" : "*2*60",
        "1m" : "*60",
        "5m" : "*60/5",
        "10m" : "*60/10",
        "30m" : "*60/30",
    }

    proc_mp=switcher.get(span, "Invalid span")
    proc_mp2=switcher2.get(span, "Invalid span")
    proc_mp3=switcher3.get(span, "Invalid span")

    return [
        {
            "scope" : "01 system",
            "spl": f"""
            search index=_introspection {optcmd} sourcetype=splunk_resource_usage component=Hostwide
            | bin _time span={span}
            | rename data.* as * 
            | eval obj="resource"
            | eval cpu=cpu_system_pct+cpu_user_pct 
            | rename _time as time
            | stats limit=0 avg(cpu) as cpu_pct, avg(mem_used) as mem_MiB by time host obj
            """
        },
        {
            "scope" : "012 ingestion",
            "spl" : f"""
            search index="_internal" {optcmd} source="*/metrics.log*"  group=per_sourcetype_thruput 
            [| rest /services/server/info |where "indexer" in(server_roles)| table host | sort host]
            | eval gb=kb/1024/1024{proc_mp2}
            | bin _time span={span}
            | eval obj="ingestion"
            | rename _time as time
            | eval host="clusterwide"
            | stats sum(gb) as ingestion_gb_per_day by time host obj
            """
        },
        {
            "scope" : "0121 ingestion",
            "spl" : f"""
            search index="_internal" {optcmd} source="*/metrics.log*"  group=per_sourcetype_thruput 
            [| rest /services/server/info |where "indexer" in(server_roles)| table host | sort host]
            | eval gb=kb/1024/1024{proc_mp2}
            | bin _time span={span}
            | eval obj="ingestion"
            | rename _time as time
            | stats sum(gb) as ingestion_gb_per_day by time host obj
            """
        },
        {
            "scope" : "0130 search",
            "spl" : f"""
            search index="_introspection"
            sourcetype=splunk_resource_usage  component=PerProcess data.search_props.role=head 
            data.search_props.sid::*  
            | eval sid = "data.search_props.sid"  
            | bin _time span=1s 
            | stats dc(sid) AS distinct_search_count by _time  
            | bin _time span={span}
            | rename _time as time
            | eval host="Clusterwide"
            | eval obj="search"
            | stats max(distinct_search_count) as concurrency_max by time host obj
            """
        },
        {
            "scope" : "013 adhoc search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_* search_id!=*subsearch* is_realtime=0 savedsearch_name=""
            | bin _time span={span}
            | eval obj="adhoc search"
            |rename _time as time
            | eval host="clusterwide"
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "0131 adhoc search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_* search_id!=*subsearch* is_realtime=0 savedsearch_name=""
            | bin _time span={span}
            | eval obj="adhoc search"
            |rename _time as time
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "014 DMA search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_scheduler_* search_id!=*subsearch* is_realtime=0 savedsearch_name=*_ACCELERATE_*
            | bin _time span={span}
            | eval obj="DMA search"
            | rename _time as time
            | eval host="clusterwide"
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "0141 DMA search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_scheduler_* search_id!=*subsearch* is_realtime=0 savedsearch_name=*_ACCELERATE_*
            | bin _time span={span}
            | eval obj="DMA search"
            | rename _time as time
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "015 ES correlation search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_scheduler_* search_id!=*subsearch* is_realtime=0 savedsearch_name="*- Rule"
            | bin _time span={span}
            | eval obj="ES correlation search"
            | rename _time as time
            | eval host="clusterwide"
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "0151 ES correlation search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_scheduler_* search_id!=*subsearch* is_realtime=0 savedsearch_name="*- Rule"
            | bin _time span={span}
            | eval obj="ES correlation search"
            | rename _time as time
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "016 ES saved search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_scheduler_* search_id!=*subsearch* is_realtime=0 savedsearch_name!="*- Rule" savedsearch_name!="_ACCELERATE_*" savedsearch_name!=""
            | bin _time span={span}
            | eval obj="ES saved search"
            | rename _time as time
            | eval host="clusterwide"
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "0161 ES saved search",
            "spl" : f"""
            search index=_audit {optcmd} 
            info=completed search_id!=*rsa_scheduler_* search_id!=*subsearch* is_realtime=0 savedsearch_name!="*- Rule" savedsearch_name!="_ACCELERATE_*" savedsearch_name!=""
            | bin _time span={span}
            | eval obj="ES saved search"
            | rename _time as time
            | stats count as count_per_hour, avg(total_run_time) as searchtime_sec by time host obj
            | eval count_per_hour=count_per_hour{proc_mp3}
            """
        },
        {
            "scope" : "02 proc",
            "spl" : f"""
            search index=_introspection {optcmd} sourcetype=splunk_resource_usage component=PerProcess
            | rename data.* as * 
            | rename process as obj
            | eval pct_cpu = pct_cpu{proc_mp}
            | eval mem_used = mem_used{proc_mp}
            | eval fd_used = fd_used{proc_mp}
            | eval t_count = t_count{proc_mp}
            | bin _time span={span}
            | rename _time as time
            | stats limit=0 sum(pct_cpu) as cpu_pct, sum(mem_used) as mem_MiB
              sum(fd_used) as fd_count, sum(t_count) as thread_count 
             by time host obj
            """,
        },
        {
            "scope": "03 proc_class",
            "spl" : f"""
            search index=_introspection {optcmd} sourcetype=splunk_resource_usage component=PerProcess 
            (
            host=sh-i-08d78ca895e0f82be*
             OR 
            host=sh-i-05c6f78a25760a5d4*
             OR 
            host=c0m1-i-0b25d7ecf8841a3b*
            OR
            host=idx-i-06b3d0c75e30d380*
            )
            | eval process = 'data.process' | eval args = 'data.args' | eval pid = 'data.pid' 
            | eval ppid = 'data.ppid' | eval elapsed = 'data.elapsed' | eval mem_used = 'data.mem_used' 
            | eval mem = 'data.mem' | eval pct_memory = 'data.pct_memory' | eval pct_cpu = 'data.pct_cpu' 
            | eval fd = 'data.fd_used' 
            | eval t_count = 'data.t_count' 
            | eval sid = 'data.search_props.sid' | eval app = 'data.search_props.app' 
            | eval label = 'data.search_props.label' | eval type = 'data.search_props.type' 
            | eval mode = 'data.search_props.mode' | eval user = 'data.search_props.user' 
            | eval role = 'data.search_props.role' 
            | eval label = if(isnotnull('data.search_props.label'), 'data.search_props.label', "") 
            | eval provenance = if(isnotnull('data.search_props.provenance'), 'data.search_props.provenance', "unknown") 
            | eval search_head = case(isnotnull('data.search_props.search_head') 
            AND 'data.search_props.role' == "peer", 'data.search_props.search_head', isnull('data.search_props.search_head') 
            AND 'data.search_props.role' == "head", "_self", isnull('data.search_props.search_head') 
            AND 'data.search_props.role' == "peer", "_unknown") 
            | eval workload_pool = if(isnotnull('data.workload_pool'), 'data.workload_pool', "UNDEFINED") 
            | eval process_class = case( process=="splunk-optimize","index service", process=="sh" 
            OR process=="ksh" OR process=="bash" OR like(process,"python%") 
            OR process=="powershell","scripted input", process=="mongod", "KVStore") 
            | eval process_class = case( process=="splunkd" 
            AND (like(args,"-p %start%") OR like(args,"service") 
            OR like(args,"%_internal_launch_under_systemd%")),"splunkd server", process=="splunkd" 
            AND isnotnull(sid) AND type=="datamodel acceleration","datamodel acceleration", process=="splunkd" 
            AND isnotnull(sid) AND type=="scheduled","scheduler searches", process=="splunkd" 
            AND isnotnull(sid) AND type=="ad-hoc","ad-hoc searches", process=="splunkd" 
            AND isnotnull(sid) AND type=="summary index","summary index", process=="splunkd" 
            AND (like(args,"fsck%") OR like(args,"recover-metadata%") 
            OR like(args,"cluster_thing")),"index service", process=="splunkd" 
            AND args=="instrument-resource-usage", "scripted input", (like(process,"python%") 
            AND like(args,"%/appserver/mrsparkle/root.py%")) 
            OR like(process,"splunkweb"),"Splunk Web", isnotnull(process_class), process_class) 
            | eval process_class = if(isnull(process_class),"other",process_class) 
            | bin _time span=10s 
            | stats 
            latest(pct_cpu) AS resource_usage_dedup 
            latest(mem_used) AS mem_usage_dedup 
            latest(fd) AS fd_usage_dedup
            latest(t_count) AS t_count_usage_dedup
            latest(process_class) AS process_class by pid, _time, host 
            | stats sum(resource_usage_dedup) AS resource_usage 
            sum(mem_usage_dedup) AS mem_usage 
            sum(fd_usage_dedup) AS fd_usage 
            sum(t_count_usage_dedup) AS t_usage  
            by _time, process_class, host 
            | bin _time span={span} 
            | rename process_class as obj
            | rename _time as time
            | stats 
            avg(resource_usage) AS "cpu_pct" 
            avg(mem_usage) AS "mem_MiB" 
            avg(fd_usage) AS "fd_count"
            avg(t_usage) AS "thread_count"
            by time, host, obj
            """
        },
        {
            "scope" : "04 crash",
            "spl" : f"""
            search index=_internal {optcmd} source=*crash* 
            | rex field=_raw "Crashing thread: (?<crash_thread>\w+)" 
            | bin _time span={span} 
            | rename crash_thread as obj
            | rename _time as time
            | stats count as crash_count by time host obj
            """
            
        },
        {
            "scope" : "05 dma_search",
            "spl" :     f"""
            search index=_internal {optcmd} sourcetype=scheduler 
            source=*/scheduler*.log search_type=datamodel_acceleration savedsearch_name=* status!=*_remote* 
            |rename savedsearch_name as obj
            |bin _time span={span}
            | rename _time as time
            | stats distinct_count(scheduled_time) as total_count,
            count(eval(status="success")) as success_count by time host obj
            | eval fail_count = total_count - success_count 
            | eval fail_ratio=fail_count/total_count*100
            """
        },
        {
            "scope" : "06 buckets_tx",
            "spl" : f"""
            search index=_audit {optcmd} (action=remote_bucket_download OR action=local_bucket_upload 
            OR action=local_bucket_evict OR action=remote_bucket_remove) info=completed cache_id="*bid|*" 
            | rename action as obj
            |bin _time span={span}
            | rename _time as time
            | stats sum(kb) as KB_per_sec by time host obj
            """
        }
  
    ]


def get_results(span='1d', optcmd=''):
    return pd.concat(
        map(get_df_melt, do_spl_list(span, optcmd))
    )