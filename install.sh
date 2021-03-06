# Install argo to the default namespace
kubectl create ns argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/stable/manifests/namespace-install.yaml

# Install a rolebinding with admin privs
kubectl create rolebinding default-admin --clusterrole=admin --serviceaccount=argo:default -n argo

# Apply a custom workflow-controller config
kubectl apply -f configmap.yaml

# Install secrets
kubectl apply -f secrets.yaml

# Install ingress
kubectl apply -f ingress.yaml

# Install basic-auth secrets
kubectl create secret generic basic-auth --from-file=auth
