import hashlib, hmac, metaworkflow.metaworkflow, os

from flask import Flask
from flask import request
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

def start_server():
  http_server = WSGIServer(('0.0.0.0', 8080), app)
  http_server.serve_forever()



@app.route('/health')
def health():
  return 'OK!'


@app.route('/webhooks/github', methods=["POST"])
def github_webhook():
  if not os.environ["SKIP_WEBHOOK_VALIDATION"] and not validate_github_webhook_secret(request):
    return "Invalid WebHook signature", 400

  payload = request.get_json()

  if "pull_request" in payload and "state" in payload["pull_request"] and payload["pull_request"]["state"] == "open" and payload["pull_request"]["draft"] != True:
    print("Webhook received (pull request, state=open)")
    metaworkflow.metaworkflow.handle_pr_push(payload)
  elif "before" in payload and "after" in payload and "ref" in payload and payload["ref"] == "refs/heads/master":
    print("Webhook received (merge to master)")
    metaworkflow.metaworkflow.handle_master_push(payload)
  else:
    print("Unhandled webhook type")
    print(payload["before"])
    print(payload["ref"])

  return "OK", 200



def validate_github_webhook_secret(request):
  digest_maker = hmac.new(os.environ["WEBHOOK_SECRET"].encode("utf-8"), bytearray(request.data), hashlib.sha1)
  if not hmac.compare_digest(digest_maker.hexdigest(), request.headers.get('X-Hub-Signature').replace("sha1=", "")):
    print("Invalid X-Hub-Signature in Github webhook call")
    return False
  return True