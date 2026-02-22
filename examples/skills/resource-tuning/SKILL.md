---
name: resource-tuning
description: Right-size CPU and memory requests/limits for workloads using metrics, VPA recommendations, and best practices.
---

# Resource Tuning

## When to use
Use this skill when the user wants to:
- Right-size pod resource requests and limits
- Reduce cluster resource waste
- Fix OOMKilled or CPU throttling issues

## Step-by-step

1. **Get current resource configuration**
   ```bash
   oc get deployment <name> -n <namespace> -o jsonpath='{.spec.template.spec.containers[*].resources}'
   ```

2. **Check actual usage with metrics**
   ```bash
   oc adm top pods -n <namespace>
   ```
   Compare actual usage against configured requests/limits.

3. **Review VPA recommendations (if VPA is installed)**
   ```bash
   oc get vpa -n <namespace>
   oc describe vpa <vpa-name> -n <namespace>
   ```
   VPA provides target, lower-bound, and upper-bound recommendations.

4. **Check for OOMKilled events**
   ```bash
   oc get events -n <namespace> --field-selector reason=OOMKilling
   ```

5. **Check for CPU throttling**
   ```bash
   oc exec <pod-name> -n <namespace> -- cat /sys/fs/cgroup/cpu/cpu.stat
   ```
   High `nr_throttled` values indicate CPU limits are too low.

6. **Apply updated resources**
   ```bash
   oc set resources deployment/<name> -n <namespace> \
     --requests=cpu=200m,memory=256Mi \
     --limits=cpu=500m,memory=512Mi
   ```

## Best practices
- Always set requests; set limits for memory (prevents OOM), consider omitting CPU limits (avoids throttling)
- Requests should reflect typical usage; limits should cover peak usage with headroom
- Use LimitRanges and ResourceQuotas at the namespace level to enforce guardrails
- Monitor with `oc adm top` or Prometheus metrics over time before making changes
