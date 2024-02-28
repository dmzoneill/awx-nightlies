import json
import subprocess

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

