from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import urllib.request, urllib.parse, urllib.error
import httplib2
from xml.dom import minidom

baseurl = 'https://10.224.18.195:8089'
userName = 'admin'
password = 'Chang3d!'

searchQuery = 'search index=_introspection sourcetype=splunk_resource_usage component=Hostwide host=sh* | rename data.* as *| eval cpu=cpu_system_pct+cpu_user_pct | timechart minspan=10s  avg(cpu) as cpu_usage by host limit=0'

# Authenticate with server.
# Disable SSL cert validation. Splunk certs are self-signed.
serverContent = httplib2.Http(disable_ssl_certificate_validation=True).request(baseurl + '/services/auth/login',
    'POST', headers={}, body=urllib.parse.urlencode({'username':userName, 'password':password}))[1]

sessionKey = minidom.parseString(serverContent).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue

# Remove leading and trailing whitespace from the search
searchQuery = searchQuery.strip()

# If the query doesn't already start with the 'search' operator or another
# generating command (e.g. "| inputcsv"), then prepend "search " to it.
if not (searchQuery.startswith('search') or searchQuery.startswith("|")):
    searchQuery = 'search ' + searchQuery
    
print(searchQuery)

# Run the search.
# Again, disable SSL cert validation.
print(httplib2.Http(disable_ssl_certificate_validation=True).request(baseurl + '/services/search/jobs','POST',
    headers={'Authorization': 'Splunk %s' % sessionKey},body=urllib.parse.urlencode({'search': searchQuery}))[1])