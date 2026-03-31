# CLO835 Employee Database — Flask App on Kubernetes

A containerized Flask web application that allows users to manage employee records stored in a MySQL database. The app runs on Kubernetes (EKS) and is deployed via a GitHub Actions CI/CD pipeline.

---

## Project Overview

This project demonstrates a full-stack cloud-native application with:

- A **Flask** web frontend for adding and retrieving employee records
- A **MySQL** database backend with persistent storage via a Kubernetes PVC
- **Docker** containerization of both the Flask app and MySQL
- **Amazon ECR** for storing Docker images
- **Kubernetes (EKS)** for orchestration
- **GitHub Actions** for automated CI/CD on pushes to `main`
- **Amazon S3** for serving a background image

---

## Application Pages

| Page | URL | Description |
|------|-----|-------------|
| Home | `/` | Displays all employees in a table |
| Add Employee | `/addemp` | Form to insert a new employee record |
| Get Employee | `/getemp` | Form to look up an employee by ID |
| About | `/about` | About page |

---

## Project Structure

```
CLO835-Project/
├── app.py                        # Flask application with all routes
├── Dockerfile                    # Docker image definition for Flask app
├── requirements.txt              # Python dependencies
├── templates/
│   ├── index.html                # Home page — employee table + navigation
│   ├── addemp.html               # Add employee form
│   ├── addempoutput.html         # Confirmation after adding employee
│   ├── getemp.html               # Get employee form
│   ├── getempoutput.html         # Employee lookup result
│   └── about.html                # About page
├── k8s/
│   ├── flask-deployment.yaml     # Flask app Deployment + Service
│   ├── mysql-deployment.yaml     # MySQL Deployment + Service
│   ├── configmap.yaml            # Non-sensitive environment variables
│   ├── secret.yaml.template      # Template for secret (never commit secret.yaml)
│   ├── pvc.yaml                  # PersistentVolumeClaim for MySQL data
│   ├── rbac.yaml                 # RBAC roles and bindings
│   └── serviceaccount.yaml       # Kubernetes ServiceAccount
└── .github/
    └── workflows/
        └── build.yaml            # GitHub Actions CI/CD pipeline
```

---

## Environment Variables

### ConfigMap (`k8s/configmap.yaml`)

| Variable | Description |
|----------|-------------|
| `STUDENT_NAME` | Name displayed on the home page |
| `DBHOST` | MySQL service name inside the cluster (`mysql-service`) |
| `DBPORT` | MySQL port (3306) |
| `DATABASE` | MySQL database name |
| `BACKGROUND_IMAGE_URL` | S3 URL for the background image |

### Secret (`k8s/secret.yaml`) — not committed to Git

| Variable | Description |
|----------|-------------|
| `DBUSER` | MySQL username |
| `DBPWD` | MySQL password |

> **Security note:** `secret.yaml` is listed in `.gitignore` and must never be committed to the repository. Use `secret.yaml.template` as a reference and create your own `secret.yaml` locally.

---

## MySQL Database Schema

```sql
CREATE TABLE IF NOT EXISTS employee (
    emp_id        INT PRIMARY KEY,
    first_name    VARCHAR(50),
    last_name     VARCHAR(50),
    primary_skill VARCHAR(100),
    location      VARCHAR(100)
);
```

> **Note:** The table is named `employee` (no 's').

---

## Deployment

### Prerequisites

- AWS CLI configured with appropriate IAM permissions
- `kubectl` connected to your EKS cluster
- Docker installed
- GitHub repository secrets set: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`

### Deploy to Kubernetes

> **Important:** `secret.yaml` is not in the repository. You must create it from the template before deploying.

**Step 1 — create your secret file from the template:**

```bash
cp k8s/secret.yaml.template k8s/secret.yaml
nano k8s/secret.yaml   # fill in your real DBUSER and DBPWD
```

**Step 2 — apply all manifests in order:**

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/flask-deployment.yaml
```

### Tear Down

```bash
kubectl delete -f k8s/flask-deployment.yaml
kubectl delete -f k8s/mysql-deployment.yaml
kubectl delete -f k8s/pvc.yaml
kubectl delete -f k8s/secret.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/rbac.yaml
kubectl delete -f k8s/serviceaccount.yaml
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/build.yaml`) triggers on every push to the `main` branch and:

1. Checks out the code
2. Configures AWS credentials from GitHub secrets
3. Logs into Amazon ECR
4. Builds and pushes the Flask Docker image to ECR (`clo835-flask-app`)

To deploy updated code, merge your changes to `main` then restart the deployment:

```bash
git checkout main
git merge your-branch
git push origin main

# After the pipeline completes:
kubectl rollout restart deployment flask-app -n final
```

---

## Troubleshooting

**"No employee data found" on home page**
- Verify the `employee` table exists: connect to the MySQL pod and run `SHOW TABLES;`
- Check Flask logs: `kubectl logs -f deployment/flask-app -n final`

**"Access denied" DB error in logs**
- The credentials in `secret.yaml` don't match what MySQL expects
- Decode the current secret to verify: `kubectl get secret mysql-secret -n final -o jsonpath='{.data.DBPWD}' | base64 --decode`
- Fix inside the MySQL pod: `ALTER USER '<your-user>'@'%' IDENTIFIED BY '<your-password>';`

**Pod not picking up new code after push**
- Force a rollout restart: `kubectl rollout restart deployment flask-app -n final`
- Verify the running image has your changes: `kubectl exec -it <pod> -n final -- grep "def addemp" /app/app.py`

---

## Author

Maedeh Ivy Nastaran — CLO835 Cloud Computing Project