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

  org = payload["repository"]["owner"]["name"]
  service_name = payload["repository"]["name"]
  branch = payload["ref"].split("/")[-1]
  commit_sha = payload["head_commit"]["id"]

  if ("before" in payload or "after" in payload):
    print("Received webhook, scaffolding metapipeline")
    print(yaml.dump(scaffold_workflow(service_name, org, branch, commit_sha)))
  else:
    print("Received webhook for unrecognised event")

  return "OK", 200

def validate_github_webhook_secret(request):
  digest_maker = hmac.new("a-secret-key".encode("utf-8"), bytearray(request.data), hashlib.sha1)
  if not hmac.compare_digest(digest_maker.hexdigest(), request.headers.get('X-Hub-Signature').replace("sha1=", "")):
    print("Invalid X-Hub-Signature in Github webhook call")
    return False
  return True

http_server = WSGIServer(('0.0.0.0', 8080), app)
http_server.serve_forever()
