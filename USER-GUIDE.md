# UCS Director to Intersight Cloud Orchestrator
## Automatic Workflow Mirroring Tool
###### A tool written in Python to automatically generate ICO Workflows that mirror the UCS Director User Experience

## User Guide

Once you have generated the JSON file from the script, you need to import it in Intersight Cloud Orchestrator (ICO).

## Import

From Intersight Cloud Orchestrator, click on `Import`, then `Browse` to select the JSON file you just created with the script. 

You can optionally select an `Organization`.<br>
Click `Next`.

Intersight will display the list of objects that will be created:

- A rollback custom task to automatically rollback UCS Director Workflows
- A reusable custom task that represents the UCSD Workflow Callout (returns the SR name from UCSD)
- A workflow that uses the reusable custom task, checks the SR execution status and extracts UCSD workflow outputs mapping them to ICO workflow outputs 
- Two batch executors to abstract the API calls to UCS Director

![Workflow Import 1](./screenshots/import1.png)

Click `Import`.

Verify all objects validated.

![Workflow Import 2](./screenshots/import2.png)

Click `Close`.

## Use the imported Workflow

You can use the workflow in ICO in a standalone mode (execute the workflow) or in a larger workflow as a nested workflow.

### Standalone Execution

![Workflow Execution 1](./screenshots/exec1.png)

The workflow will have the same inputs as the UCSD counterpart. <br>
Additionally, you will need to select a UCSD target which will be the system actually executing the automation:

![Workflow Execution 2](./screenshots/exec2.png)

If the execution is succeeded, UCSD SR outputs will be mapped to ICO Workflow Outputs:

![Workflow Execution 3](./screenshots/exec3.png)

View from UCS Director for this workflow execution:

![UCSD](./screenshots/ucsd_in_out.png)

### Nested Workflow Execution

You can use the UCSD workflow mirror in ICO as part of a larger workflow.<br> 
Mirrored UCSD workflows can be found under the `UCS Director Workflows` folder:

![Nested Workflow](./screenshots/largerwf1.png)

To leverage a mixed ICO and UCSD Worfklow, you can map ICO task outputs to UCSD Workflow Inputs and/or UCSD Workflow Outputs to ICO task inputs:

![Nested Workflow Mapping](./screenshots/mapinputs.png)


## Rollback Workflow Execution

Select a successful `Request` and click `Rollback`

![Rollback 1](./screenshots/rollback1.png)

Select `Rollback` again to confirm

![Rollback 2](./screenshots/rollback2.png)

UCSD View for Rollback

![UCSD Rollback](./screenshots/ucsd_rollback.png)

## Change Workflow Inputs and Outputs in UCS Director

There are cases when due to a change of business requirements, the UCS Director workflow inputs or outputs needs to be modified (i.e. add another mandatory input).

After the change on UCSD side, just re-run the script and import again selecting `Replace` when prompted. This will re-sync both workflows. <br>
Execution history will be preserved on ICO.

![Workflow Import Replace](./screenshots/replace.png)

## Open Caveats and Limitations

- All ICO Workflow Inputs are strings
	- <b>Workaround:</b> manual pass after import to customize with appropriate data types if needed

- All ICO Workflows Inputs are mandatory
	- <b>Workaround:</b> manual pass to unflag as mandatory optional inputs

- Resulting ICO Workflow inputs value must be exactly one word (no spaces allowed as ICO reusable task input substitution will break the URL). 
	- <b>Workaround:</b> use %20 instead of spaces

- Rollback in ICO rollbacks the whole UCSD SR (you can't select what tasks to rollback for UCSD in the current implementation)
	- <b>Workaround:</b> rollback from UCSD if granular rollback is required 
