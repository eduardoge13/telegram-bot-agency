# 🔐 Security Checklist & Best Practices

## ✅ Current Security Status

### What's SECURE:
- ✅ Bot tokens stored in Secret Manager (not in code)
- ✅ Google credentials stored in Secret Manager 
- ✅ Sensitive files properly gitignored
- ✅ Production config separated from dev config
- ✅ Environment-based deployments

### What's IMPROVED:
- ✅ Removed duplicate code from deploy.sh
- ✅ Fixed script to use prod_config.env correctly
- ✅ No hardcoded tokens/credentials in deployment script

## 🚨 CRITICAL Security Actions Required

### 1. Verify .gitignore is Working
```bash
# Check what files are being tracked:
git status

# These files should NEVER appear in git status:
# - telegram_dev_token.txt
# - prod_setup/telegram_prod_token.txt  
# - credentials.json
# - prod_setup/prod_config.env
# - .env

# If any of these show up, they're NOT being ignored!
```

### 2. Remove Any Sensitive Data from Git History
```bash
# Check if sensitive files were ever committed:
git log --all --full-history -- telegram_dev_token.txt
git log --all --full-history -- credentials.json
git log --all --full-history -- prod_setup/prod_config.env

# If these commands show commits, you need to clean git history!
```

### 3. Verify Secret Manager Access
```bash
# Check current secrets:
gcloud secrets list --project=promising-node-469902-m2

# Should show:
# - google-credentials-json
# - telegram-bot-token (production)
# - telegram-bot-token-dev (development)
```

## 🛡️ Additional Security Measures

### 1. Google Cloud IAM Security

**Service Account Permissions (Current):**
- `promising-node-469902-m2-compute@developer.gserviceaccount.com`
- Has: Secret Manager accessor, Cloud Run invoker

**Recommendations:**
```bash
# Create dedicated service account for bot (more secure):
gcloud iam service-accounts create telegram-bot-sa \
    --display-name="Telegram Bot Service Account" \
    --project=promising-node-469902-m2

# Grant only necessary permissions:
gcloud projects add-iam-policy-binding promising-node-469902-m2 \
    --member="serviceAccount:telegram-bot-sa@promising-node-469902-m2.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Update Cloud Run to use dedicated service account:
# (Add to deploy.sh: --service-account=telegram-bot-sa@promising-node-469902-m2.iam.gserviceaccount.com)
```

### 2. Network Security

**Current:** Bot is publicly accessible (--allow-unauthenticated)

**Options:**
```bash
# Option A: Keep public (for Telegram webhooks) - CURRENT
--allow-unauthenticated

# Option B: Restrict access (for polling only)
--no-allow-unauthenticated
# Then add IAM binding for specific users
```

### 3. Telegram Bot Security

**Current Settings:**
- Bot tokens in Secret Manager ✅
- Authorized users list in environment ✅

**Additional Security:**
```python
# Add to bot code (already implemented):
def _is_authorized_user(self, user_id: int) -> bool:
    authorized_users = os.getenv('AUTHORIZED_USERS', '').split(',')
    return str(user_id) in authorized_users

# Consider adding:
# - Rate limiting per user
# - Command logging with user tracking
# - Blacklist for malicious users
```

### 4. Secret Rotation

**Setup automatic secret rotation:**
```bash
# Create rotation schedule (recommended: every 90 days)
gcloud secrets add-version telegram-bot-token --data-file=new-token.txt

# Test new version before making it active
gcloud secrets versions access 2 --secret=telegram-bot-token

# Activate new version
gcloud secrets versions activate 2 --secret=telegram-bot-token
```

### 5. Monitoring & Alerting

**Current:** Basic Cloud Run logs

**Enhanced Security Monitoring:**
```bash
# Set up alerts for:
# - Failed authentication attempts
# - Unusual API usage patterns  
# - Error rate spikes
# - Secret access patterns

# Enable Cloud Audit logs:
gcloud logging sinks create telegram-bot-audit \
    bigquery.googleapis.com/projects/promising-node-469902-m2/datasets/security_logs \
    --log-filter='protoPayload.serviceName="secretmanager.googleapis.com"'
```

## 📋 Pre-Production Security Checklist

### Before EVERY Production Deployment:

- [ ] **No sensitive data in code**: `grep -r "token\|key\|secret\|password" . --exclude-dir=.git`
- [ ] **All secrets in Secret Manager**: `gcloud secrets list --project=promising-node-469902-m2`
- [ ] **Gitignore working**: `git status` shows no sensitive files
- [ ] **Service account has minimal permissions**: Only what's needed
- [ ] **Authorized users list updated**: Only current team members
- [ ] **Production config file secure**: Not in git history
- [ ] **Test deployment in dev first**: Always test before prod

### Production Environment Hardening:

- [ ] **Dedicated service account**: Not using default compute account
- [ ] **Network restrictions**: Consider VPC if possible  
- [ ] **Resource limits**: CPU/Memory limits set appropriately
- [ ] **Timeout settings**: Prevent resource exhaustion
- [ ] **Rate limiting**: Implement if high traffic expected

## 🔍 Security Monitoring Commands

### Daily Security Checks:
```bash
# Check for unauthorized access attempts:
gcloud logging read "resource.type=cloud_run_revision AND severity>=WARNING" \
    --project=promising-node-469902-m2 --limit=50

# Monitor secret access:
gcloud logging read "protoPayload.serviceName=secretmanager.googleapis.com" \
    --project=promising-node-469902-m2 --limit=10

# Check service health:
curl -s https://telegram-bot-agency-xxxxx.us-central1.run.app/health | jq .
```

### Weekly Security Review:
```bash
# Review IAM permissions:
gcloud projects get-iam-policy promising-node-469902-m2

# Check service account keys:
gcloud iam service-accounts keys list \
    --iam-account=telegram-bot-sa@promising-node-469902-m2.iam.gserviceaccount.com

# Review secret versions:
gcloud secrets versions list telegram-bot-token --project=promising-node-469902-m2
```

## 🚨 Security Incident Response

### If Bot Token Compromised:
1. **Immediately disable** old token in @BotFather
2. **Create new token** and update Secret Manager
3. **Redeploy** bot with new token: `./deploy.sh prod`
4. **Check logs** for unauthorized usage
5. **Review** authorized users list

### If Service Account Compromised:
1. **Disable service account** immediately
2. **Create new service account** with minimal permissions
3. **Update deployment** to use new account
4. **Audit access logs** for unauthorized activity
5. **Rotate all secrets** accessed by compromised account

## 📊 Security Metrics to Monitor

1. **Authentication failures** per hour
2. **Unusual API call patterns** (volume, timing)
3. **Error rates** above normal baseline
4. **Resource usage spikes** (potential DoS)
5. **Unauthorized user attempts** (not in authorized list)
6. **Secret access frequency** (should be predictable)

---

**Remember:** Security is ongoing, not a one-time setup. Review and update regularly!