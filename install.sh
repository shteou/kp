# Install argo to the default namespace
kubectl create ns argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/stable/manifests/namespace-install.yaml

# Install a rolebinding with admin privs
kubectl create rolebinding default-admin --clusterrole=admin --serviceaccount=argo:default -n argo

# Apply a custom workflow-controller config
kubectl apply -f configmap.yaml
