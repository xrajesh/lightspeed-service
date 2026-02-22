---
name: troubleshoot-networking
description: Diagnose and resolve OpenShift cluster networking issues including DNS failures, Service connectivity, and Ingress problems.
---

# Troubleshoot Networking

## When to use
Use this skill when the user reports:
- Pods cannot resolve DNS names
- Services are unreachable from other pods
- Ingress / Route traffic is failing
- ClusterOperators are degraded due to networking

## Step-by-step

1. **Check DNS resolution inside the cluster**
   ```bash
   oc run dns-test --rm -it --restart=Never --image=registry.access.redhat.com/ubi9/ubi-minimal -- nslookup kubernetes.default.svc.cluster.local
   ```
   If this fails, DNS is broken at the cluster level.

2. **Inspect the DNS operator and CoreDNS pods**
   ```bash
   oc get clusteroperator dns
   oc get pods -n openshift-dns
   ```
   Look for pods in CrashLoopBackOff or not Ready.

3. **Check upstream resolver configuration**
   ```bash
   oc get dns.operator.openshift.io/default -o yaml
   ```
   Verify `spec.upstreamResolvers` points to a reachable DNS server.

4. **Verify Service endpoints**
   ```bash
   oc get endpoints <service-name> -n <namespace>
   ```
   Empty endpoints mean no healthy pods are backing the service.

5. **Check NetworkPolicy**
   ```bash
   oc get networkpolicy -n <namespace>
   ```
   Overly restrictive policies can block legitimate traffic.

6. **Inspect Ingress / Router pods**
   ```bash
   oc get pods -n openshift-ingress
   oc logs -n openshift-ingress <router-pod>
   ```

## Common fixes
- Patch DNS back to working upstream: `oc patch dns.operator.openshift.io/default --type=merge -p '{"spec":{"upstreamResolvers":{"upstreams":[{"type":"SystemResolvConf"}]}}}'`
- Restart CoreDNS pods: `oc delete pods -n openshift-dns -l dns.operator.openshift.io/daemonset-dns`
- Scale the router if pods are missing: `oc scale --replicas=2 deployment/router-default -n openshift-ingress`
