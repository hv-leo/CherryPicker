import json


# If there is no assignee, return all SP cases for the Service Pack.
# If there is, return assignee's SP cases for the Service Pack.
def get_sp_cases(jira, service_pack, assignee):
    if assignee:
        sps = jira.search_issues('fixVersion="' + service_pack + '" and assignee="' + assignee +
                                 '" and (status="Open" or status="In Progress")')
    else:
        sps = jira.search_issues('fixVersion="' + service_pack +
                                 '" and (status="Open" or status="In Progress")')
    return ["[" + sp.key + "] " + sp.fields.summary for sp in sps]


# Get base case development data.
# I had to hijack the JIRA session, since we don't have this feature on JIRA API.
def get_data(jira, sp_key):
    # Get base case commits:
    base_bug = get_base_bug(jira, sp_key)
    commits_url = jira._options['server'] + "/rest/dev-status/1.0/issue/detail?"
    commits_url += "issueId=" + base_bug.id
    commits_url += "&applicationType=github&dataType=repository&_=157263009880"
    sess_get = jira._session.get
    response = sess_get(commits_url)
    return json.loads(response.content)


# Get SP Case's base bug.
def get_base_bug(jira, sp_key):
    sp_case = jira.issue(sp_key)
    base_bug_key = sp_case.fields.summary.split(" ")[2]
    base_bug = jira.issue(base_bug_key)
    return base_bug
