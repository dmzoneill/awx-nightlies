import json
import subprocess

def needs_rebase(pr_number):
    # Run 'gh pr view' to get information about the pull request
    result = subprocess.run(["gh", "pr", "view", str(pr_number), "--json", "merge_state,head_ref"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error fetching pull request information: {result.stderr}")
        return False

    # Parse the JSON output
    pr_info = json.loads(result.stdout)

    # Check if the pull request needs rebasing
    return pr_info.get("merge_state", {}).get("status") == "behind"

def rebase_pull_request(pr_number):
    # Check if rebase is needed
    if needs_rebase(pr_number):
        # Run the 'gh pr rebase' command
        subprocess.run(["gh", "pr", "rebase", str(pr_number)])
        print("Rebase completed successfully.")
    else:
        print("No rebase needed.")

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

    all_prs = get_all_prs(owner, repo)

    if open_prs is not None:
        print(f"Checking all PR's for rebasing")
        for pr in all_prs:
            print(f"#{pr['number']} - {pr['title']}")
            rebase_pull_request(owner, repo, pr['number'])
