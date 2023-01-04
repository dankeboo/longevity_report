import splunklib.client as client

host = 'https://10.224.18.195:8089'
host = '10.224.18.195'

service = client.connect(host=host, username='admin', password='Chang3d!', autologin=True)