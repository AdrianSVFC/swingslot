#!/usr/bin/env bash
# One-time Google Cloud setup for SwingSlot (Jira GOLF-73, GOLF-74).
# Run it once in Cloud Shell. It is safe to read: it only creates resources, it never deletes.
# Written with help from Claude (AI); reviewed and run by Adrian.
#
# What it creates
#   - APIs: Cloud Run, Artifact Registry, IAM credentials/STS (keyless GitHub login),
#     Secret Manager, Cloud Monitoring and Logging
#   - Artifact Registry Docker repository "swingslot" (stores the images CI builds)
#   - Service account "swingslot-runtime": the identity the running app uses (no project roles)
#   - Service account "github-deployer": what GitHub Actions uses to deploy, with only
#     Cloud Run Admin + Artifact Registry Writer + permission to act as swingslot-runtime
#   - Secret "flask-secret-key": a random Flask SECRET_KEY that never leaves Google Cloud
#   - Workload Identity Federation pool/provider so GitHub Actions can log in WITHOUT a JSON key.
#     Only workflows from the AdrianSVFC/swingslot repository are accepted.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-project-92a4b1e0-49fb-4dc8-bd3}"
REGION="${REGION:-us-central1}"
GITHUB_REPO="${GITHUB_REPO:-AdrianSVFC/swingslot}"

DEPLOYER="github-deployer@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME="swingslot-runtime@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

echo "== Enabling APIs"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com secretmanager.googleapis.com \
  monitoring.googleapis.com logging.googleapis.com cloudresourcemanager.googleapis.com

echo "== Artifact Registry repository"
gcloud artifacts repositories describe swingslot --location "$REGION" >/dev/null 2>&1 ||
  gcloud artifacts repositories create swingslot --repository-format=docker \
    --location "$REGION" --description "SwingSlot Docker images built by GitHub Actions"

echo "== Service accounts"
gcloud iam service-accounts describe "$RUNTIME" >/dev/null 2>&1 ||
  gcloud iam service-accounts create swingslot-runtime --display-name "SwingSlot Cloud Run runtime"
gcloud iam service-accounts describe "$DEPLOYER" >/dev/null 2>&1 ||
  gcloud iam service-accounts create github-deployer --display-name "GitHub Actions deployer"

# Least privilege for the deployer
for ROLE in roles/run.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$DEPLOYER" \
    --role "$ROLE" --condition=None --quiet >/dev/null
done
# The deployer may only "act as" the runtime account (not every account in the project)
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME" \
  --member "serviceAccount:$DEPLOYER" --role roles/iam.serviceAccountUser --quiet >/dev/null

echo "== Flask SECRET_KEY in Secret Manager"
gcloud secrets describe flask-secret-key >/dev/null 2>&1 ||
  openssl rand -hex 32 | gcloud secrets create flask-secret-key --data-file=- --replication-policy=automatic
gcloud secrets add-iam-policy-binding flask-secret-key --member "serviceAccount:$RUNTIME" \
  --role roles/secretmanager.secretAccessor --quiet >/dev/null

echo "== Workload Identity Federation (keyless login for GitHub Actions)"
gcloud iam workload-identity-pools describe github --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create github --location global --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers describe swingslot-repo --location global \
  --workload-identity-pool github >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools providers create-oidc swingslot-repo --location global \
    --workload-identity-pool github --display-name "SwingSlot GitHub repo" \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition "assertion.repository == '${GITHUB_REPO}'"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOYER" --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/attribute.repository/${GITHUB_REPO}" \
  --quiet >/dev/null

echo ""
echo "== Done. Add these as GitHub repository VARIABLES (Settings > Secrets and variables > Actions > Variables):"
echo "GCP_PROJECT_ID=${PROJECT_ID}"
echo "GCP_REGION=${REGION}"
echo "GCP_WIF_PROVIDER=projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/providers/swingslot-repo"
echo "GCP_DEPLOY_SA=${DEPLOYER}"
echo "GCP_RUNTIME_SA=${RUNTIME}"
