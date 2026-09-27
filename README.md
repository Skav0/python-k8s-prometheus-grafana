# Project Documentation: Monitoring a Python Application on Amazon EKS with Prometheus & Grafana

This project documents the end-to-end implementation of instrumenting, deploying, and monitoring a Python web application running on an **Amazon EKS (Elastic Kubernetes Service)** cluster using **Prometheus** and **Grafana**.

---

## 📁 Repository Structure

```text
python-k8s-prometheus-grafana/
├── app/
│   ├── app.py            # Python web application with Prometheus metrics
│   ├── Dockerfile        # Container image definition
│   └── requirements.txt  # Python dependencies (Flask, prometheus-client)
├── images/
│   ├── APP.png           # Web app UI screenshot
│   └── Grafana.png       # Grafana metric visualization screenshot
├── k8s/
│   └── deployment.yaml   # Kubernetes Deployment & Service with scrape annotations
└── README.md             # Project documentation
```

---

## 🏗 System Architecture

The implemented architecture consists of four primary components:

1. **Python Application**: A web service built using Flask and instrumented with `prometheus_client` to expose custom metrics via the `/metrics` endpoint.
2. **Amazon EKS Cluster**: The managed Kubernetes environment hosting the application workload and the monitoring infrastructure.
3. **Prometheus**: Deployed via the `kube-prometheus-stack` Helm chart. It handles target discovery using Service annotations and scrapes application metrics at defined intervals.
4. **Grafana**: Serves as the visualization engine, querying time-series data from Prometheus to display application performance, request rates, and network statistics.

---

## 🛠 Tools & Environment

The following command-line utilities and tools were configured to build and manage this project:

* **AWS CLI**: Authenticated to manage AWS credentials and interface with the Amazon EKS cluster.
* **kubectl**: Used for cluster interaction and manifest deployment.
* **Helm**: Utilized as the package manager to deploy the Prometheus and Grafana stack.
* **Docker**: Used to containerize the Python web application and push the image to a container registry.

---

## 🚀 Implementation Workflow

### 1. EKS Cluster Configuration
Cluster access was established locally by updating the `kubeconfig` via the AWS CLI:

```bash
aws eks update-kubeconfig --region <your-region> --name <your-eks-cluster-name>
```

Cluster node connectivity was verified:

```bash
kubectl get nodes
```

### 2. Monitoring Stack Deployment
The `kube-prometheus-stack` was installed into the cluster using Helm:

```bash
# Added the prometheus-community repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Deployed Prometheus and Grafana
helm install my-kube-prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```

Pod initialization was verified to ensure all monitoring components reached a `Running` state:

```bash
kubectl get pods --namespace monitoring -l app.kubernetes.io/instance=my-kube-prometheus-stack
```

### 3. Application Containerization & Image Publishing
The Python application was packaged using Docker and pushed to the container registry:

```bash
cd app/

# Built the container image
docker build -t <your-dockerhub-username>/python-prometheus-app:v1 .


# Pushed image to registry
docker push <your-dockerhub-username>/python-prometheus-app:v1


=> Checkout my image:
https://hub.docker.com/repository/docker/skavi0/pyt-prom/tags/v1/sha256-c81d357762bfba679a434aa87223fac5af97273445275678d27fbc1c9df1b753


```

### 4. Kubernetes Workload Deployment
The application was deployed to the EKS cluster using the manifest configured with Prometheus scrape annotations (`prometheus.io/scrape: "true"`):

```bash
kubectl apply -f k8s/deployment.yaml
```

Deployment status was checked to confirm active pods:

```bash
kubectl get pods -l app=python-app
```

---

## 📊 Verification & Metric Access

### 1. Python Application & Metrics Validation
Port forwarding was established to verify local access to the application and its `/metrics` endpoint:

```bash
kubectl port-forward svc/python-app-service 5000:5000
```

* **Application Endpoint**: `http://localhost:5000`
* **Prometheus Metrics Endpoint**: `http://localhost:5000/metrics`

### 2. Prometheus Target Verification
Port forwarding was used to access the Prometheus web interface:

```bash
kubectl port-forward --namespace monitoring svc/my-kube-prometheus-stack-prometheus 9090:9090
```

Inside the UI at `http://localhost:9090`, the `python-app-service` was confirmed as an active target under **Status -> Targets**.

### 3. Grafana Visualization Setup
Port forwarding was initiated for Grafana:

```bash
kubectl port-forward --namespace monitoring svc/my-kube-prometheus-stack-grafana 3000:80
```

The administrative password was retrieved via Kubernetes secrets:

```bash
kubectl get secret --namespace monitoring my-kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

Logged into `http://localhost:3000` as `admin` to build dashboards and execute metric queries.

---

## 📈 Key PromQL Queries Evaluated

* **Container Network Receive Bytes**: `container_network_receive_bytes_total` is a monotonically increasing counter of the total number of bytes received by a container over its network interface. The `pod` label limits the result to one pod. Replace `You_pod_name` with the current pod name:
  ```promql
  container_network_receive_bytes_total{pod="You_pod_name"}
  ```

  Example for this deployment:

  ```promql
  container_network_receive_bytes_total{pod="python-app-65ff6969f7-c2q8s"}
  ```
