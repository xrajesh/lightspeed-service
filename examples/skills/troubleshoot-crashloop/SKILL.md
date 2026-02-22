---
name: troubleshoot-crashloop
description: Diagnose pods stuck in CrashLoopBackOff by inspecting logs, events, resource limits, and image pull issues.
---

# Troubleshoot CrashLoopBackOff

## When to use
Use this skill when a user reports pods in `CrashLoopBackOff` status.

## Step-by-step

1. **Identify the failing pod**
   ```bash
   oc get pods -n <namespace> | grep CrashLoop
   ```

2. **Read the pod events**
   ```bash
   oc describe pod <pod-name> -n <namespace>
   ```
   Look at the `Events` section for OOMKilled, image pull errors, or probe failures.

3. **Check container logs**
   ```bash
   oc logs <pod-name> -n <namespace> --previous
   ```
   The `--previous` flag shows logs from the last crashed container instance.

4. **Check resource limits**
   ```bash
   oc get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources}'
   ```
   If the container was OOMKilled, increase memory limits.

5. **Verify the image is pullable**
   ```bash
   oc get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'
   ```
   Try pulling the image manually to rule out registry issues.

6. **Check liveness / readiness probes**
   Misconfigured probes (wrong port, too-short timeout) cause restarts.

## Common fixes
- OOMKilled → increase `resources.limits.memory`
- Image pull error → verify image tag, registry credentials (`oc get secret`)
- Probe failure → adjust `initialDelaySeconds`, `timeoutSeconds`, or endpoint
- Missing config → ensure ConfigMaps and Secrets referenced by the pod exist
