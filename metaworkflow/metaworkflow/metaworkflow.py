import yaml

def handle_pr_push(payload):
  (branch, pr_number, commit_sha, org, repo) = extract_pr_info(payload)
  print(yaml.dump(scaffold_workflow(repo, org, f"pr-{pr_number}", commit_sha)))


def handle_master_push(payload):
  (commit_sha, org, repo) = extract_master_info(payload)
  print(yaml.dump(scaffold_workflow(repo, org, "master", commit_sha)))


def extract_pr_info(payload):
  pull_request = payload["pull_request"]
  head = pull_request["head"]

  branch = head["ref"]
  pr_number = pull_request["number"]
  before_commit = head["sha"]
  org = head["repo"]["owner"]["login"]
  repo = head["repo"]["name"]

  return (branch, pr_number, before_commit, org, repo)


def extract_master_info(payload):
  repository = payload["repository"]

  before_commit = payload["before"]
  org = repository["owner"]["name"]
  repo = repository["name"]

  return (before_commit, org, repo)


def make_template(name, image, command, args):
  return {
    "name": name,
    "container": {
      "image": image,
      "command": command,
      "args": args,
      "resources": {
        "limits": {
          "memory": "32Mi",
          "cpu": "100m"
        }
      },
      "env": [{
        "name": "GITHUB_CREDS",
        "valueFrom": { 
          "secretKeyRef": {
            "name": "github",
            "key": "creds"
          }
        }
      }]
    }
  }


def git_clone_template(service_name, org):
  return make_template("clone", "alpine/git", ["git"], ["clone", f"https://github.com/{org}/{service_name}.git"])


def scaffold_workflow(service_name, org, branch, commit_sha):
  return {
    "apiVersion": "argoproj.io/v1alpha1",
    "kind": "Workflow",
    "metadata": {
      "generatename": f"metapipeline-{service_name}-{branch}-{commit_sha[0:7]}-"
    }, "spec": {
      "entrypoint": "clone",
      "templates": [git_clone_template(service_name, org)]
    }
  }