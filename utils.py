import requests
import json
import urllib
import re

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class UCSDApi():

    def __init__(self, ucsd_ip, ucsd_key):
        self.headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Cloupia-Request-Key": ucsd_key
        }
        self.ucsd_ip = ucsd_ip

    def replace_non_alpha(self, string):
        x = re.sub("[^0-9a-zA-Z ]+", "", string)
        return re.sub(' +', ' ', x)

    def get_folders(self):
        query = '%7B%22param0%22%3A10%2C%22param1%22%3Anull%2C%22param2%22%3A%22WORKFLOWS-T46%22%7D'
        response = requests.get('https://{0}/app/api/rest?formatType=json&opName=userAPIGetTabularReport&opData={1}'.format(self.ucsd_ip,query), verify=False, headers=self.headers)
        folders = []
        for wf in json.loads(response.content)['serviceResult']['rows']:
            folders.append(wf['Workflow_Folder'])
        list_set = set(folders)
        unique_list = (list(list_set))
        folders = []
        for x in unique_list:
            folders.append(x)
        folders.sort()
        return folders
    
    def get_workflows(self):
        query = '%7B%22param0%22%3A10%2C%22param1%22%3Anull%2C%22param2%22%3A%22WORKFLOWS-T46%22%7D'
        response = requests.get('https://{0}/app/api/rest?formatType=json&opName=userAPIGetTabularReport&opData={1}'.format(self.ucsd_ip,query), verify=False, headers=self.headers)
        wf_list = []
        for wf in json.loads(response.content)['serviceResult']['rows']:
            wf_list.append(wf['Workflow_Folder'])
        wf_list.sort()
        return len(wf_list)

    def get_workflows_from_folder(self, folder):
        query = '{param0:"' + folder + '"}'
        response = requests.get('https://{0}/app/api/rest?formatType=json&opName=userAPIGetWorkflows&opData={1}'.format(self.ucsd_ip,query), verify=False, headers=self.headers)
        wf_list = []
        for wf in json.loads(response.content)['serviceResult']:
            wf_list.append(wf['name'])
        wf_list.sort()
        return wf_list

    def ico_web_executor_url_builder(self, workflow_name, input_list):
        input_payload = ""
        for item in input_list:
            input_payload += '{"name":"' + item + '","value":"' + '{{.global.task.input.' + item.replace(" ", "") + '}}' + '"},'
        input_payload = input_payload[:-1]
        payload = '{param0:"' + workflow_name + '",param1:{"list": [' + input_payload + ']},param2: -1}'
        enc_payload = urllib.parse.quote(payload)
        a = enc_payload.replace("%7B%7B","{{")
        b = a.replace("%7D%7D","}}")
        return '/app/api/rest?formatType=json&opName=userAPISubmitWorkflowServiceRequest&opData={}'.format(b)

    def get_workflow_inputs(self, workflow_name):
        query = '{param0:"' + workflow_name + '"}'
        enc_query = urllib.parse.quote(query)
        response = requests.get('https://{0}/app/api/rest?formatType=json&opName=userAPIGetWorkflowInputs&opData={1}'.format(self.ucsd_ip,enc_query), verify=False, headers=self.headers)
        return json.dumps(json.loads(response.content), indent=4, sort_keys=True)

    def get_workflow_outputs(self, workflow_name):
        query = '{param0:"' + workflow_name + '"}'
        enc_query = urllib.parse.quote(query)
        response = requests.get('https://{0}/app/api/rest?formatType=json&opName=workflow:userAPIGetWorkflowOutputDefinition&opData={1}'.format(self.ucsd_ip,enc_query), verify=False, headers=self.headers)
        return json.dumps(json.loads(response.content), indent=4, sort_keys=True)

''' Sample Workflow Execution Payload:
{
  "param0": "Workflow Name",
  "param1": {
    "list": [
      {
        "name": "Input1",
        "value": "value1"
      },
      {
        "name": "Input2",
        "value": "value2"
      },
      {
        "name": "Input3",
        "value": "value3"
      }
    ]
  },
  "param2": -1
}
'''