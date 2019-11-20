import json
import os
import re

from github import Github, GithubException
from jira import JIRA, JIRAError

import git as g
from requests.exceptions import MissingSchema

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

        # - - - - - - - - - - - - - - - - - - - - -
        # Merge Masters
        self.master1 = None
        self.master2 = None

        self.jira_connection = None
        self.github_connection = None
        self.backports = None

        # Create the entire GUI program
        self.gui = GUI(self)

        # Start the GUI event loop
        self.gui.window.mainloop()

    # Get SP cases for a given assignee and service pack.
    def get_sp_cases(self):
        self.gui.clear_logs()
        self.jira_url = self.gui.jira_url_input.get().strip()
        self.jira_username = self.gui.jira_user_input.get().strip()
        self.jira_password = self.gui.jira_password_input.get()
        self.service_pack = self.gui.service_pack_input.get().strip()
        self.assignee = self.gui.assignee_input.get().strip()

        if self.assignee:
            self.gui.log_info("Getting " + self.assignee + "'s SP cases for " + self.service_pack + "...")
        else:
            self.gui.log_info("Getting SP cases for " + self.service_pack + "...")

        # Connect to JIRA.
        try:
            self.gui.log_info("Connecting to JIRA...")
            self.jira_connection = JIRA(server=self.jira_url, basic_auth=(self.jira_username, self.jira_password))
        except MissingSchema as me:
            self.gui.log_error("Unable to connect to JIRA: " + str(me))
            return
        except JIRAError as je:
            self.gui.log_error("Unable to connect to JIRA: " + je.text)
            return

        # Get Open and In Progress SP cases.
        try:
            sp_cases = JIRAUtils.get_sp_cases(self.jira_connection, self.service_pack, self.assignee)
        except JIRAError as je:
            self.gui.log_error("Unable to fetch SP Cases: " + je.text)
            return

        # Update list of SP cases to be backported.
        self.gui.update_sp_list(sp_cases)
        self.gui.log_info(str(len(sp_cases)) + " SP cases added.")

    # Backport the selected SP cases.
    def backport(self):
        self.gui.clear_logs()
        self.gui.log_info("Starting to Backport...")

        # Connect to GitHub.
        self.github_username = self.gui.github_user_input.get().strip()
        self.github_password = self.gui.github_password_input.get()
        try:
            self.github_connection = Github(self.github_username, self.github_password)
            upstream_user = self.github_connection.get_user('pentaho')
        except GithubException as ge:
            self.gui.log_error("Unable to connect to GitHub: " + ge.data['message'])
            self.gui.log_info("Done!")
            return

        self.base_folder = self.gui.base_folder_input.get().strip()

        # Go through all SP cases
        sp_keys = [sp.split(' ')[0].replace('[', '').replace(']', '') for sp in self.gui.backports_listbox.get()]
        for sp_key in sp_keys:

            # Apply the Begin Work transition for the SP case.
            issue = self.jira_connection.issue(sp_key)
            self.jira_connection.assign_issue(issue, self.jira_username)
            if issue.fields.status.name == 'Open':
                self.jira_connection.transition_issue(issue.key, '11')

            # Get data from the JIRA Developer plugin.
            # Get Base Bug commits.
            self.gui.log_info("Backporting " + sp_key + "!")
            base_bug = JIRAUtils.get_base_bug(self.jira_connection, sp_key)
            raw_data = JIRAUtils.get_data(self.jira_connection, base_bug)
            repositories = raw_data['detail'][0]['repositories']
            rep_names = [rep['name'] for rep in repositories]

            # Search for missing commits.
            # Find "PR: <git-pr-link>" patterns in JIRA case comments.
            jira_comments = [[re.search(r'(?<=PR:).*', body).group(0) for body in
                              comment.body.encode("ascii", errors="ignore").decode().replace("\r\n", "\n").replace("\r", "\n").split('\n') if
                              re.search(r'(?<=PR:).*', body) is not None] for comment in
                             self.jira_connection.issue(base_bug.key).fields.comment.comments]
            links_in_comments = [item.strip() for sublist in jira_comments for item in sublist]

            # Check if there are missing commits in JIRA Developer plugin.
            for rep_name in rep_names:
                for not_missing_link in links_in_comments:
                    # Commits are on JIRA Developer Plugin.
                    if rep_name in not_missing_link:
                        break

                    # Commits are missing
                    try:
                        upstream_repo = upstream_user.get_repo(rep_name)
                    except GithubException:
                        upstream_repo = self.github_connection.get_user('webdetails').get_repo(rep_name)
                    try:
                        pr = upstream_repo.get_pull(not_missing_link.split('/')[-1])
                    except:
                        continue
                    for commit in pr.get_commits().get_page(0):
                        rep_name = commit.html_url.split('/')[4]
                        sha = commit.html_url.split('/')[-1]
                        repositories.append({'name': rep_name,
                                             'commits': [
                                                 {'message': "Missing Commit", 'id': sha, 'url': commit.html_url,
                                                  'authorTimestamp': 1}]})
            if not rep_names:
                for missing_link in links_in_comments:
                    # All commits are missing
                    rep_name = missing_link.split('/')[-3]
                    pr_nr = missing_link.split('/')[-1]
                    pr_nr = int(''.join([i for i in pr_nr if i.isdigit()]))
                    try:
                        upstream_repo = upstream_user.get_repo(rep_name)
                    except GithubException:
                        upstream_repo = self.github_connection.get_user('webdetails').get_repo(rep_name)
                    try:
                        pr = upstream_repo.get_pull(pr_nr)
                    except:
                        continue
                    for commit in pr.get_commits().get_page(0):
                        rep_name = commit.html_url.split('/')[4]
                        sha = commit.html_url.split('/')[-1]
                        repositories.append({'name': rep_name,
                                             'commits': [
                                                 {'message': "Missing Commit", 'id': sha, 'url': commit.html_url,
                                                  'authorTimestamp': 1}]})

            # Initialize JIRA comment.
            jira_comment = "*Attention: This is the outcome of an automated process!*"
            jira_comment += "\nPRs:"

            # Go through all repositories.
            for repository in repositories:
                has_merge_conflicts = False
                self.gui.log_info("Creating the " + sp_key + " branch in " + repository['name'] + ".")

                # Check if we have the repository in place.
                repo_path = os.path.join(os.path.normpath(self.base_folder), repository['name'])
                if os.path.exists(repo_path):
                    repo = g.Repo.init(repo_path)
                else:
                    self.gui.log_error("Couldn't find repository in " + repo_path)
                    continue

                # Create SP branch.
                git = repo.git
                base_version_branch = self.service_pack.split('-')[1].split(' ')[0]
                sp_version_branch = self.service_pack.split(' ')[1].replace('(', '').replace(')', '')
                git.fetch('--all')
                try:
                    # Make sure we don't have a SP branch on origin.
                    git.push("origin", '--delete', sp_key)
                except g.GitCommandError:
                    pass
                finally:
                    try:
                        # Checkout to version branch.
                        git.checkout(base_version_branch)
                    except g.GitCommandError as gce:
                        git.checkout('-b', base_version_branch, 'origin/' + base_version_branch)
                    # Pull all version branch changes.
                    git.pull('upstream', base_version_branch)

                    try:
                        # Make sure we don't have a SP branch locally.
                        git.branch("-D", sp_key)
                    except g.GitCommandError:
                        pass
                    finally:
                        git.checkout('-b', sp_key)

                # List of commits to be cherry-picked.
                commits = repository['commits']
                urls = []
                # Order commits by date, so we maintain the chronology of events.
                commits.sort(key=sort_by_timestamp)
                commit_message = '[' + sp_key + '] ' + self.jira_connection.issue(sp_key).fields.summary

                # Go through all commits.
                for commit in commits:
                    # Don't cherry-pick merge PR commits.
                    if not commit['message'].startswith("Merge pull request"):
                        # Cherry-pick base case commits.
                        sha = commit['id']
                        urls.append(commit['url'])
                        self.gui.log_info("Cherry-picking " + sha + ".")
                        try:
                            git.cherry_pick(sha)
                        except g.GitCommandError as gce:
                            # Flag that we have merge conflicts, so we can signalize that on the jira comment later.
                            has_merge_conflicts = True
                            self.gui.log_error("Unable to cherry-pick '" + sha + "': " + gce.stderr.strip())
                            # Delete changes.
                            git.reset('--hard')
                            break
                        # Rename commits with backport message.
                        git.commit('--amend', '-m', commit_message)

                # Proceed with the backport, if we don't have conflicts
                base_pr = version_pr = None
                if has_merge_conflicts is False:
                    try:
                        # Push changes.
                        self.gui.log_info("Pushing commits to " + sp_key + " branch.")
                        git.push("origin", sp_key)
                    except g.GitCommandError as gce:
                        self.gui.log_error("Unable to push changes to origin " + sp_key + " branch: " + gce.stderr.strip())
                        git.checkout('master')
                        git.branch("-D", sp_key)
                        self.gui.log_info("Done with " + repository['name'] + "!")

                    # Build PR message.
                    self.master1 = self.gui.master1_input.get()
                    self.master2 = self.gui.master2_input.get()
                    pr_message = "**Attention: This is the outcome of an automated process!**"
                    pr_message += "\nMerge Masters: " + self.master1 + " and " + self.master2 + "\n"
                    pr_message += "Cherry-picks:\n"
                    for url in urls:
                        pr_message += "* " + url + "\n"

                    # Build and send Pull Request.
                    self.gui.log_info("Opening PRs for " + sp_key + ".")
                    try:
                        upstream_repo = upstream_user.get_repo(repository['name'])
                    except GithubException:
                        upstream_repo = self.github_connection.get_user('webdetails').get_repo(repository['name'])

                    # For version branch
                    try:
                        upstream_repo.get_branch(base_version_branch)
                        base_pr = upstream_repo.create_pull(commit_message, pr_message, base_version_branch,
                                                            '{}:{}'.format(self.github_username, sp_key), True)
                    except GithubException as ge:
                        if ge.status == 422:
                            self.gui.log_error(
                                "Unable to submit PR for " + sp_key + " in " + base_version_branch + " branch: " +
                                ge.data['errors'][0]['message'])
                        else:
                            self.gui.log_error(
                                "Unable to submit PR for " + sp_key + " in " + base_version_branch + " branch: " +
                                ge.data['message'])
                    else:
                        self.gui.log_info("Opened Pull Request in " + base_version_branch + " branch")

                    # For SP branch
                    try:
                        upstream_repo.get_branch(sp_version_branch)
                        version_pr = upstream_repo.create_pull(commit_message, pr_message, sp_version_branch,
                                                               '{}:{}'.format(self.github_username, sp_key), True)
                    except GithubException as ge:
                        if ge.status == 422:
                            self.gui.log_error(
                                "Unable to submit PR for " + sp_key + " in " + sp_version_branch + " branch: " +
                                ge.data['errors'][0]['message'])
                        else:
                            self.gui.log_warn(
                                "Unable to submit PR for " + sp_key + " in " + sp_version_branch + " branch: " +
                                ge.data['message'])
                    else:
                        self.gui.log_info("Opened Pull Request in " + sp_version_branch + " branch")

                # Delete branch and Move to next repository.
                self.gui.log_info("Deleting " + sp_key + " branch...")
                git.checkout('master')
                git.branch("-D", sp_key)
                self.gui.log_info("Done with " + repository['name'] + "!")

                # Add PR links in the JIRA case
                self.gui.log_info("Adding PR links in " + sp_key + "...")
                jira_comment += "\n* " + repository['name'] + ":"
                if base_pr:
                    jira_comment += "\n** " + base_version_branch + ": " + base_pr.html_url
                elif has_merge_conflicts:
                    jira_comment += " There are conflicts that need to be manually treated."
                if version_pr:
                    jira_comment += "\n** " + sp_version_branch + ": " + version_pr.html_url

            # Add pull-request-sent label
            issue.fields.labels.append(u"pull-request-sent")
            issue.update(fields={"labels": issue.fields.labels})

            # Move issue to block status
            self.jira_connection.transition_issue(sp_key, '61', comment=jira_comment)

            # Move to next SP case.
            self.gui.log_info("Done with " + sp_key + "!")


def sort_by_timestamp(val):
    return val['authorTimestamp']


# Start application
MainController()
