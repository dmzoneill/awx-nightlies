import json
import subprocess
# import os
# import sys
# import requests
# from pprint import pprint
# from graphql import oid

# def update_pull_request_branch(owner, repo, pr_number, base_branch):
#     # GitHub API endpoint for GraphQL
#     graphql_endpoint = f"https://api.github.com/graphql"

#     # GraphQL query to get the current pull request information
#     query = f"""
#     query {{
#       repository(owner: "{owner}", name: "{repo}") {{
#         pullRequest(number: {pr_number}) {{
#           headRefName
#           headRepository {{
#             id
#             nameWithOwner
#           }}
#         }}
#       }}
#     }}
#     """

#     access_token = os.getenv("GH_TOKEN")

#     # Make the GraphQL request to get current branch information
#     response = requests.post(graphql_endpoint, json={"query": query}, headers={"Authorization": f"Bearer {access_token}"})
#     response_data = response.json()

#     pprint(response_data)

#     # Extract relevant information from the response
#     current_branch = response_data['data']['repository']['pullRequest']['headRefName']
#     head_repository_id = response_data['data']['repository']['pullRequest']['headRepository']['id']
#     head_repository_name = response_data['data']['repository']['pullRequest']['headRepository']['nameWithOwner']

#     # GraphQL mutation to update the pull request branch

#     mutation = f"""
#     mutation {{
#     updatePullRequestBranch(
#         input: {{
#         pullRequestId: "{pr_number}",
#         expectedHeadOid: {oid({head_repository_id})},
#         expectedBaseOid: "{base_branch}"
#         }}
#     ) {{
#         pullRequest {{
#         id
#         headRefName
#         }}
#     }}
#     }}
#     """

#     # Make the GraphQL request to update the pull request branch
#     response = requests.post(graphql_endpoint, json={"query": mutation}, headers={"Authorization": f"Bearer {access_token}"})
#     response_data = response.json()

#     pprint(response_data)

#     # Extract information from the response
#     updated_branch = response_data['data']['updatePullRequestBranch']['pullRequest']['headRefName']

#     sys.exit(1)

#     print(f"Pull Request branch updated from '{current_branch}' to '{updated_branch}'.")

# def needs_rebase(owner, repo, pr_number):
#     # Run 'gh pr view' to get information about the pull request
#     result = subprocess.run(["gh", "pr", "view", str(pr_number), "--json", "mergeStateStatus", "--repo", f"{owner}/{repo}"], capture_output=True, text=True)

#     if result.returncode != 0:
#         print(f"Error fetching pull request information: {result.stderr}")
#         return False

#     # Parse the JSON output
#     pr_info = json.loads(result.stdout)

#     valid_states = ["BEHIND" , "MERGEABLE", "BLOCKED"]

#     # Check if the pull request needs rebasing
#     return pr_info.get("mergeStateStatus", "DIRTY") in valid_states

# def rebase_pull_request(owner, repo, pr_number):
#     # Check if rebase is needed
#     if needs_rebase(owner, repo, pr_number):
#         # Run the 'gh pr rebase' command
#         subprocess.run(["gh", "pr", "rebase", str(pr_number), "--repo", f"{owner}/{repo}"])
#         print("Rebase completed successfully.")
#     else:
#         print("No rebase needed.")

def get_open_prs(owner, repo, label='blocked'):
    command = f'gh pr list -R https://github.com/{owner}/{repo}/ --search "draft:false" --json number,title,labels'

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        prs_data = json.loads(result.stdout)

        # Filter PRs based on label
        open_prs = [pr for pr in prs_data if label not in pr.get('labels', [])]

        return open_prs
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON output. {e}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing the command. Command failed with exit code {e.returncode}.")
        return None
    
def get_all_prs(owner, repo):
    command = f'gh pr list -R https://github.com/{owner}/{repo}/ --json number,title,labels'

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        prs_data = json.loads(result.stdout)

        return prs_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON output. {e}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing the command. Command failed with exit code {e.returncode}.")
        return None

def check_pr_status(owner, repo, pull_request_number):
    pr_url = f'https://github.com/{owner}/{repo}/pull/{pull_request_number}'
    command = f'gh pr checks {pr_url}'

    result = subprocess.run(command, shell=True, capture_output=True)

    # Check the return code of the command
    if result.returncode != 0:
        print(f"Checks failed {result.returncode}.")
        return False

    print("All checks have passed.")
    return True

def update_pull_request_to_draft(owner, repo, pull_request_number):
    pr_url = f'https://github.com/{owner}/{repo}/pull/{pull_request_number}'
    command = f'gh pr ready {pr_url} --undo'
    
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Pull request #{pull_request_number} successfully set to draft status.")
    except subprocess.CalledProcessError as e:
        print(f"Error updating pull request status. Command failed with exit code {e.returncode}")

if __name__ == "__main__":
    owner = 'ansible'
    repo = 'awx'
    label = 'blocked'
    
    open_prs = get_open_prs(owner, repo, label)

    if open_prs is not None:
        print(f"Open pull requests not in draft status and without the '{label}' label:")
        for pr in open_prs:
            print(f"#{pr['number']} - {pr['title']}")
            check_status = check_pr_status(owner, repo, pr['number'])
            print(f"Combined success status: {check_status}")

            if check_status is not None and not check_status:
                update_pull_request_to_draft(owner, repo, pr['number'])

    # all_prs = get_all_prs(owner, repo)

    # if all_prs is not None:
    #     print(f"Checking all PR's for rebasing")
    #     for pr in all_prs:
    #         print(f"#{pr['number']} - {pr['title']}")
    #         update_pull_request_branch(owner, repo, pr['number'], "devel")
