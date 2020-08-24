# CodeBuild / Argo pipeline bridge


## S3 artifact storage

Create a secret of the form:

```
apiVersion: v1
kind: Secret
metadata:
  name: my-s3-credentials
type: Opaque
data:
  accessKey: b64_access_key
  secretKey: b64_secret_key
```

Replace `<your endpoint>` in `configmap.yaml` with an S3 endpoint, e.g.
  `my-artifact-url.s3.fr-par.scw.cloud`

Replace `<your access key>` and `<your secret key>` in `secrets.yaml`

## Ingress

Replace `<your host name>` in `ingress.yaml` with the desired hostname of the argo-server

Create an htpasswd file called auth.

## Installation

Run `./install.sh` !!!
