from utils import UCSDApi
import json
import sys
from time import sleep
import argparse

example = '''Example:
pip install -r requirements.txt

# Run in non-interactive mode (will return the JSON file to import in ICO):
python ucsd_to_ico.py -u 10.1.1.1 -k 052BF5DFD9204541D25DFBAC27CCE7FA -w "My Workflow" 

# Run in interactive mode (will present a menu from which you can select the target workflow to mirror):
python ucsd_to_ico.py -u 10.1.1.1 -k 052BF5DFD9204541D25DFBAC27CCE7FA

'''
description = '''Mirrors UCS Director Workflows in Intersight Cloud Orchestrator
Returns a JSON file which can be imported in ICO.

rtortori@cisco.com'''

parser = argparse.ArgumentParser(prog='python ucsd_to_ico.py',
                                 description=description,
                                 epilog=example,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-u", "--ucsd", help="IP or FQDN of the Target UCSD Host", required=True)
parser.add_argument("-k", "--key", help="UCSD API Key", required=True)
parser.add_argument("-w", "--workflow", help="Name of the UCSD Workflow to Mirror", required=False)
args = parser.parse_args()

ucsd_ip = args.ucsd
ucsd_key = args.key
if args.workflow:
    workflow_name = args.workflow
else:
    workflow_name = ""

# Initialize Lists
input_list = []
output_list = []

# Initialize UCSD Connection
print('')
print('Initializing connection to UCSD {}'.format(ucsd_ip))
print()
ucsd = UCSDApi(ucsd_ip, ucsd_key)

############ Show Menu If workflow name is not explicit ############

if workflow_name == "":
    menu_folders = {}
    menu_workflows = {}
    folders = ucsd.get_folders()

    for index, folder in enumerate(folders):
        menu_folders[index + 1] = folder

    def print_menu():
        for key in menu_folders.keys():
            print (key, '--', menu_folders[key] )

    def print_menu_workflows():
        for key in menu_workflows.keys():
            print (key, '--', menu_workflows[key] )

    def get_wf(folder):
        print()
        print('Folder: ' + folder)
        wf_list = ucsd.get_workflows_from_folder(folder)
        wf_list.sort()
        for index, workflow in enumerate(wf_list):
            menu_workflows[index + 1] = workflow
        while(True):
            print_menu_workflows()
            option = ''
            try:
                option = int(input('Select Workflow (0 to Exit): '))
            except:
                print('Please enter a number ...')
        
            if option == 0:
                print('Goodbye.')
                exit()
            elif option in menu_workflows.keys():
                workflow = menu_workflows[option]
                return workflow
            else:
                print()
                print('Invalid Choice. Please enter a number between 1 and {}'.format(str(len(menu_workflows))))
                print()
                sleep(2)
        

    while(True):
        print_menu()
        option = ''
        try:
            option = int(input('Select Folder (0 to Exit): '))
        except:
            print('Wrong input. Please enter a number ...')
        
        if option == 0:
            print('Goodbye.')
            exit()
        elif option in menu_folders.keys():
            workflow_name = get_wf(menu_folders[option])
            break
        else:
            print('Invalid Choice. Please enter a number between 1 and {}'.format(str(len(menu_folders))))
            sleep(2)

###################################


try:
    # Get Workflow Inputs and Outputs
    print()
    print('Fetching Target workflow inputs and outputs for workflow: {}'.format(workflow_name))
    inputs = json.loads(ucsd.get_workflow_inputs(workflow_name))
    outputs = json.loads(ucsd.get_workflow_outputs(workflow_name))
except:
    print("ERROR: Can't connect to UCSD. Check your UCSD IP or hostname as well as your API Key. UCSD IP: " + ucsd_ip)
    print('Quitting.')
    sys.exit(1)

if inputs['serviceError']:
    print(inputs['serviceError'])
    sys.exit(1)

# Extract Inputs And Outputs

for input in inputs['serviceResult']['details']:
    input_list.append(input['label'])

print()
print('Workflow Inputs:')
print('\n'.join('- {}'.format(k) for k in input_list))
print()

for output in outputs['serviceResult']['workflowOutputFieldList']:
    output_list.append(output['outputFieldLabel'])

print()
print('Workflow Outputs:')
print('\n'.join('- {}'.format(k) for k in output_list))
print()

# Open template file
with open('wf_template.json', 'r') as file :
  filedata = file.read()

# Load template as dict
json_template = json.loads(filedata)

# Normalize Task and Workflow Names replacing non alphanumeric characters
desc = "Invokes the {} Workflow from UCS Director".format(workflow_name)
normalized_wf_name = ucsd.replace_non_alpha(workflow_name)
normalized_wf_ref_name = ucsd.replace_non_alpha(workflow_name.replace(" ", ""))

''' Update Task Definition '''
json_template[9]['Body']['Label'] = normalized_wf_name
json_template[9]['Body']['Name'] = normalized_wf_ref_name
json_template[9]['Body']['Description'] = desc
# Load Existing Input Definitions List (Task Definition)
td_id_list = json_template[9]['Body']['Properties']['InputDefinition']
# Render Inputs (Task Definition)
json_template[9]['Body']['Properties']['InputDefinition'] = ucsd.render_input_body(td_id_list, input_list)

''' Update Workflow Definition '''
json_template[10]['Body']['Label'] = normalized_wf_name
json_template[10]['Body']['Name'] = normalized_wf_ref_name
json_template[10]['Body']['Description'] = desc
json_template[10]['Body']['Tasks'][0]['NextTask'] = normalized_wf_ref_name + "1"
json_template[10]['Body']['Tasks'][4]['InputParameters']['Url'] = "/app/api/rest?formatType=json&opName=userAPIGetServiceRequestWorkFlow&opData=%7Bparam0%3A{{.global." + normalized_wf_ref_name + "1.output.ServiceRequest}}%7D"
json_template[10]['Body']['Tasks'][6]['InputParameters']['Url'] = "/app/api/rest?formatType=json&opName=servicerequest:userAPIGetServiceRequestOutputDetails&opData=%7Bparam0%3A{{.global." + normalized_wf_ref_name + "1.output.ServiceRequest}}%7D"
json_template[10]['Body']['Tasks'][7]['Label'] = normalized_wf_name
json_template[10]['Body']['Tasks'][7]['Name'] = normalized_wf_ref_name + "1"
json_template[10]['Body']['Tasks'][7]['TaskDefinitionName'] = normalized_wf_ref_name
json_template[10]['Body']['UiRenderingData']['Positions'][-1]['Name'] = normalized_wf_ref_name + "1"
# Load Existing Input Definitions List (Workflow Definition)
wd_id_list = json_template[10]['Body']['InputDefinition']
# Render Inputs (Workflow Definition)
json_template[10]['Body']['InputDefinition'] = ucsd.render_input_body(wd_id_list, input_list)
# Load Existing Output Definitions List (Workflow Definition)
wd_od_list = json_template[10]['Body']['OutputDefinition']
# Render Outputs (Workflow Definition)
json_template[10]['Body']['OutputDefinition'] = ucsd.render_output_body(wd_od_list, output_list)

# Load Output Parameters (Workflow Definition)
wd_op_dict = json_template[10]['Body']['OutputParameters']

# Create WorkflowDefinition:OutputParameters body
for index, output in enumerate(output_list):
    wd_op_dict[ucsd.replace_non_alpha(output.replace(" ", ""))] = "${InvokeGenericWebApi3.output.Parameters." + ucsd.replace_non_alpha(output.replace(" ", "")) + "}"

# Render Output Parameters (Workflow Definition)
json_template[10]['Body']['OutputParameters'] = wd_op_dict

# If the target workflow has no outputs, skip output creation on rendered ICO workflow
if len(output_list) != 0:
    # Load WorkflowDefinition:CheckSRTask:ResponseParser List
    json_template[10]['Body']['Tasks'][6]['InputParameters']['ResponseParser'] = {}
    json_template[10]['Body']['Tasks'][6]['InputParameters']['ResponseParser']['Parameters'] = []
    wd_rp_list = json_template[10]['Body']['Tasks'][6]['InputParameters']['ResponseParser']['Parameters']

    # Create WorkflowDefinition:CheckSRTask:ResponseParser body
    for index, output in enumerate(output_list):
        wd_rp_list.append(
            {
            "Name": "{}".format(ucsd.replace_non_alpha(output.replace(" ", ""))),
            "Path": "$.serviceResult.workflowOutputDetails[{}].outputFieldValue".format(index),
            "Type": "string"
            }
        )

    # Render WorkflowDefinition:CheckSRTask:ResponseParser Body
    json_template[10]['Body']['Tasks'][6]['InputParameters']['ResponseParser']['Parameters'] = wd_rp_list
else: 
    print('No Outputs Retrieved, skipping Response Parser Generation')
    print()

# Load WorkflowDefinition:CustomTask:InputMapping List
wd_ct_im_dict = json_template[10]['Body']['Tasks'][7]['InputParameters']

# Render WorkflowDefinition:CustomTask:InputMapping body
for index, input in enumerate(input_list):
    wd_ct_im_dict['{}'.format(ucsd.replace_non_alpha(input.replace(" ", "")))] = "${workflow.input." + "{}".format(ucsd.replace_non_alpha(input.replace(" ", ""))) + "}"

# Set WorkflowDefinition:CustomTask:InputMapping body
json_template[10]['Body']['Tasks'][7]['InputParameters'] = wd_ct_im_dict

''' Update Batch Executor Definition '''
json_template[-1]['Body']['Description'] = desc
json_template[-1]['Body']['Name'] = normalized_wf_name
json_template[-1]['Body']['TaskDefinition']['Selector'] = "Name eq \"{}\" and Version eq 1".format(normalized_wf_ref_name)
# Set Url to Execute Remote Workflow
json_template[-1]['Body']['Batch'][0]['Url'] = ucsd.ico_web_executor_url_builder(workflow_name, input_list)

print('Exporting ICO Workflows and Tasks...')
with open('{}-ucsd-to-ico.json'.format(workflow_name.replace(" ", "")), 'w') as rendered_workflow_file:
    json.dump(json_template, rendered_workflow_file)
    print('File exported: {}-ucsd-to-ico.json'.format(workflow_name.replace(" ", "")))