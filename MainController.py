import logging
import os

from github import Github
from jira import JIRA

import git as g
import JIRAUtils
from GUI import GUI


class MainController:
    def __init__(self):
        # - - - - - - - - - - - - - - - - - - - - -
        # JIRA Credentials
        self.jira_url = None
        self.jira_username = None
        self.jira_password = None

        # - - - - - - - - - - - - - - - - - - - - -
        # GitHub Credential
        self.github_username = None
        self.github_password = None

        # - - - - - - - - - - - - - - - - - - - - -
        # Backport Fields
        self.service_pack = None
        self.assignee = None
        self.base_folder = None

        self.jira_connection = None
        self.github_connection = None
        self.backports = None

        # Create the entire GUI program
        self.gui = GUI(self)

        # Start the GUI event loop
        self.gui.window.mainloop()

    def get_sp_cases(self):
        self.gui.clear_logs()
        self.jira_url = self.gui.jira_url_input.get().strip()
        self.jira_username = self.gui.jira_user_input.get().strip()
        self.jira_password = self.gui.jira_password_input.get()
        self.service_pack = self.gui.service_pack_input.get().strip()
        self.assignee = self.gui.assignee_input.get().strip()

        if self.assignee:
            logging.info("Getting " + self.assignee + "'s SP cases for " + self.service_pack + "...")
        else:
            logging.info("Getting SP cases for " + self.service_pack + "...")

        self.jira_connection = JIRA(server=self.jira_url, basic_auth=(self.jira_username, self.jira_password))
        sp_cases = JIRAUtils.get_sp_cases(self.jira_connection, self.service_pack, self.assignee)
        self.gui.update_sp_list(sp_cases)
        logging.info(str(len(sp_cases)) + " SP cases added.")

    def backport(self):
        self.gui.clear_logs()
        self.github_username = self.gui.github_user_input.get().strip()
        self.github_password = self.gui.github_password_input.get()
        self.github_connection = Github(self.github_username, self.github_password)
        self.base_folder = self.gui.base_folder_input.get().strip()

        # Go through all SP cases
        sp_keys = [sp.split(' ')[0].replace('[', '').replace(']', '') for sp in self.gui.backports_listbox.get()]
        logging.info("Starting to Backport...")

        for sp_key in sp_keys:
            logging.info("Backporting " + sp_key + "!")
            raw_data = JIRAUtils.get_data(self.jira_connection, sp_key)
            repositories = raw_data['detail'][0]['repositories']

            for repository in repositories:
                logging.info("Creating the " + sp_key + " branch in " + repository['name'] + ".")

                # Verify repository path.
                repo_path = self.base_folder + repository['name']
                if os.path.exists(repo_path):
                    repo = g.Repo.init(repo_path)
                else:
                    logging.error("Couldn't find repository in " + repo_path)
                    continue

                # Create SP branch.
                git = repo.git
                base_version_branch = self.service_pack.split('-')[1].split(' ')[0]
                git.checkout(base_version_branch)
                git.pull('upstream', base_version_branch)
                try:
                    git.checkout('-b', sp_key)
                except g.GitCommandError as gce:
                    logging.error("Failed to create branch: " + gce.stderr.strip())
                    continue

                # Cherry-Pick commits.
                base_bug = JIRAUtils.get_base_bug(self.jira_connection, sp_key)
                commits = repository['commits']
                # Order commits by creation date.
                commits.sort(key=sort_by_timestamp)
                for commit in commits:
                    if commit['message'].startswith("[" + base_bug.key + "]"):
                        # Cherry-pick base case commits.
                        sha = commit['id']
                        logging.info("Cherry-picking " + sha + ".")
                        git.cherry_pick(sha)
                        # Rename commits with backport message.
                        commit_message = '[' + sp_key + '] ' + self.jira_connection.issue(sp_key).fields.summary
                        git.commit('--amend', '-m', commit_message)
                git.push("origin", sp_key)


def sort_by_timestamp(val):
    return val['authorTimestamp']


# Start application
MainController()
