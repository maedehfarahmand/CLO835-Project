# CLO835 Final Project — Employee Management App on AWS EKS

A containerized full-stack web application that demonstrates cloud-native deployment on Amazon EKS. The app allows users to manage employee records through a Flask web interface backed by a MySQL database, with images stored in Amazon S3 and infrastructure managed via Kubernetes.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Deployment](#setup--deployment)
  - [1. Configure GitHub Secrets](#1-configure-github-secrets)
  - [2. Create ECR Repositories](#2-create-ecr-repositories)
  - [3. Provision the EKS Cluster](#3-provision-the-eks-cluster)
  - [4. Build & Push Docker Images](#4-build--push-docker-images)
  - [5. Deploy to Kubernetes](#5-deploy-to-kubernetes)
- [Environment Variables](#environment-variables)
- [Application Features](#application-features)
- [CI/CD Pipeline](#cicd-pipeline)
- [Kubernetes Resources](#kubernetes-resources)
- [Local Development](#local-development)

---

## Architecture Overview

```
GitHub Actions (CI/CD)
        │
        ▼
Amazon ECR (Flask + MySQL images)
        │
        ▼
Amazon EKS Cluster (us-east-1)
  ├── Namespace: final
  ├── Flask Deployment  ──► LoadBalancer Service (port 80 → 81)
  │       └── Pulls background image from S3
  └── MySQL Deployment  ──► ClusterIP Service (port 3306)
          └── Backed by PersistentVolumeClaim (2Gi gp2)
```

On every push to `main`, GitHub Actions builds both Docker images, pushes them to ECR, and they are ready to be pulled by EKS. Configuration is injected via ConfigMaps and Secrets, keeping credentials out of the codebase.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Application | Python 3.9, Flask 2.2 |
| Database | MySQL 8.0 |
| Container Runtime | Docker |
| Container Registry | Amazon ECR |
| Orchestration | Amazon EKS (Kubernetes 1.35) |
| Cloud Storage | Amazon S3 (background image) |
| CI/CD | GitHub Actions |
| Node Type | t3.small (2 nodes) |

---

## Project Structure

```
CLO835-Project/
├── app.py                        # Flask application
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Flask app image
├── Dockerfile_mysql              # Custom MySQL image with init script
├── mysql.sql                     # Database & table initialization SQL
├── eks_config.yaml               # eksctl cluster configuration
├── templates/
│   ├── index.html                # Home — employee list
│   ├── addemp.html               # Add employee form
│   ├── addempoutput.html         # Add employee confirmation
│   ├── getemp.html               # Get employee form
│   ├── getempoutput.html         # Employee detail view
│   └── about.html                # About page
├── k8s/
│   ├── flask-deployment.yaml     # Flask Deployment + LoadBalancer Service
│   ├── mysql-deployment.yaml     # MySQL Deployment + ClusterIP Service
│   ├── configmap.yaml            # Non-sensitive app configuration
│   ├── secret.yaml               # MySQL credentials (base64-encoded)
│   ├── pvc.yaml                  # PersistentVolumeClaim for MySQL data
│   ├── rbac.yaml                 # ClusterRole + ClusterRoleBinding
│   └── serviceaccount.yaml       # Kubernetes Service Account
└── .github/
    └── workflows/
        └── build.yaml            # CI/CD pipeline
```

---

## Prerequisites

- AWS CLI configured with appropriate credentials
- [`eksctl`](https://eksctl.io/) installed
- `kubectl` installed and configured
- Docker installed (for local builds)
- GitHub repository with Actions enabled

---

## Setup & Deployment

### 1. Configure GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_SESSION_TOKEN` | AWS session token (if using temporary credentials) |

### 2. Create ECR Repositories

```bash
aws ecr create-repository --repository-name clo835-flask-app --region us-east-1
aws ecr create-repository --repository-name clo835-mysql --region us-east-1
```

### 3. Provision the EKS Cluster

```bash
eksctl create cluster -f eks_config.yaml
```

This creates a managed EKS cluster named `clo835` in `us-east-1` with 2 `t3.small` worker nodes. Update your kubeconfig after the cluster is ready:

```bash
aws eks update-kubeconfig --name clo835 --region us-east-1
```

### 4. Build & Push Docker Images

Pushing to `main` triggers the GitHub Actions pipeline automatically. To build manually:

```bash
# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push Flask app
docker build -t clo835-flask-app -f Dockerfile .
docker tag clo835-flask-app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/clo835-flask-app:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/clo835-flask-app:latest

# Build and push MySQL
docker build -t clo835-mysql -f Dockerfile_mysql .
docker tag clo835-mysql:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/clo835-mysql:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/clo835-mysql:latest
```

### 5. Deploy to Kubernetes

```bash
# Create the namespace
kubectl create namespace final

# Apply all manifests
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/flask-deployment.yaml

# Get the external LoadBalancer URL
kubectl get svc flask-service -n final
```

Navigate to the `EXTERNAL-IP` shown for `flask-service` in your browser.

---

## Environment Variables

The application is configured entirely through environment variables injected by Kubernetes:

| Variable | Source | Description |
|---|---|---|
| `DBHOST` | Deployment env / ConfigMap | MySQL service hostname |
| `DBUSER` | Secret | MySQL username |
| `DBPWD` | Secret | MySQL password |
| `DATABASE` | ConfigMap | Database name (`employees`) |
| `BACKGROUND_IMAGE_URL` | ConfigMap | S3 URI for background image |
| `STUDENT_NAME` | ConfigMap | Name displayed in the UI |
| `APP_COLOR` | ConfigMap | UI background color (hex) |

---

## Application Features

| Route | Method | Description |
|---|---|---|
| `/` | GET | Home page — lists all employees |
| `/addemp` | GET | Add employee form |
| `/addemp` | POST | Submit new employee record |
| `/getemp` | GET/POST | Search employee form |
| `/fetchdata` | POST | Retrieve employee by ID |
| `/about` | GET | About page |

The background image is optionally downloaded from an S3 bucket at startup if `BACKGROUND_IMAGE_URL` begins with `s3://`.

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/build.yaml`) triggers on every push to `main`:

1. Checks out the code
2. Configures AWS credentials from GitHub Secrets
3. Logs into Amazon ECR
4. Builds and pushes the Flask app image tagged with both the commit SHA and `latest`
5. Builds and pushes the MySQL image with the same tags

---

## Kubernetes Resources

| Resource | Name | Namespace | Purpose |
|---|---|---|---|
| Deployment | `flask-app` | `final` | Runs the Flask web server |
| Deployment | `mysql` | `final` | Runs the MySQL database |
| Service | `flask-service` | `final` | Exposes Flask externally via LoadBalancer |
| Service | `mysql-service` | `final` | Internal ClusterIP for MySQL |
| ConfigMap | `app-config` | `final` | Non-sensitive environment config |
| Secret | `mysql-secret` | `final` | Database credentials |
| PVC | `mysql-pvc` | `final` | 2Gi persistent storage for MySQL data |
| ServiceAccount | `clo835` | `final` | Identity for Flask pods |
| ClusterRole | `CLO835` | — | Permissions to manage namespaces |
| ClusterRoleBinding | `clo835-binding` | — | Binds role to service account |