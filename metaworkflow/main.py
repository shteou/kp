#!/usr/bin/env python
import hashlib, hmac, os, yaml

from flask import Flask
from flask import request

from gevent.pywsgi import WSGIServer

app = Flask(__name__)

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


@app.route('/health')
def health():
    return 'OK!'

@app.route('/webhooks/github', methods=["POST"])
def github_webhook():
  if not validate_github_webhook_secret(request):
    return "Invalid WebHook signature", 400

  payload = request.get_json()

  if "pull_request" in payload and "state" in payload["pull_request"] and payload["pull_request"]["state"] == "open" and payload["pull_request"]["draft"] != True:
    print("Webhook received (pull request, state=open)")
    handle_pr_push(payload)
  elif "before" in payload and "after" in payload and "ref" in payload and payload["ref"] == "refs/heads/master":
    print("Webhook received (merge to master)")
    handle_master_push(payload)
  else:
    print("Unknown webhook type")
    print(payload["before"])
    print(payload["ref"])

  return "OK", 200

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
  before_commit = payload["before"]
  org = head["repo"]["owner"]["login"]
  repo = head["repo"]["name"]

  return (branch, pr_number, before_commit, org, repo)

def extract_master_info(payload):
  repository = payload["repository"]

  before_commit = payload["before"]
  org = repository["owner"]["name"]
  repo = repository["name"]

  return (before_commit, org, repo)
  

def validate_github_webhook_secret(request):
  digest_maker = hmac.new("a-secret-key".encode("utf-8"), bytearray(request.data), hashlib.sha1)
  if not hmac.compare_digest(digest_maker.hexdigest(), request.headers.get('X-Hub-Signature').replace("sha1=", "")):
    print("Invalid X-Hub-Signature in Github webhook call")
    return False
  return True

http_server = WSGIServer(('0.0.0.0', 8080), app)
http_server.serve_forever()
