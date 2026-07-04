import urllib.request, json
url = 'https://api.github.com/repos/pattarish-web/sangkan-clean/actions/runs?per_page=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    for run in data.get('workflow_runs', []):
        print(f"Name: {run.get('name')}, Status: {run.get('status')}, Conclusion: {run.get('conclusion')}, Msg: {run.get('head_commit', {}).get('message')[:50]}")
except Exception as e:
    print(e)
