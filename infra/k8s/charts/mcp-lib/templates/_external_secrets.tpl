{{- define "mcp-lib.externalSecrets.name" -}}
{{- $ext := default (dict) .Values.externalSecrets -}}
{{- if (get $ext "existingSecretName") -}}
{{- get $ext "existingSecretName" -}}
{{- else if (get $ext "secretName") -}}
{{- get $ext "secretName" -}}
{{- else -}}
mycontextprotocol-external
{{- end -}}
{{- end -}}

{{- define "mcp-lib.externalSecrets.envFrom" -}}
{{- $ext := default (dict) .Values.externalSecrets -}}
{{- if (default true (get $ext "enabled")) -}}
- secretRef:
    name: {{ include "mcp-lib.externalSecrets.name" . }}
{{- end -}}
{{- end -}}

{{- define "mcp-lib.externalSecrets.validate" -}}
{{- $ext := default (dict) .Values.externalSecrets -}}
{{- $enabled := default true (get $ext "enabled") -}}
{{- if and $enabled (not (get $ext "existingSecretName")) (not (get $ext "create")) -}}
{{- fail "externalSecrets.existingSecretName or externalSecrets.create must be set when externalSecrets.enabled is true" -}}
{{- end -}}
{{- end -}}

{{- define "mcp-lib.externalSecrets.render" -}}
{{- $ext := default (dict) .Values.externalSecrets -}}
{{- include "mcp-lib.externalSecrets.validate" . -}}
{{- if and (default true (get $ext "enabled")) (get $ext "create") (not (get $ext "existingSecretName")) -}}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "mcp-lib.externalSecrets.name" . }}
  namespace: {{ .Release.Namespace }}
type: Opaque
stringData:
{{- range $key, $val := (default (dict) (get $ext "data")) }}
  {{ $key }}: {{ $val | quote }}
{{- end }}
{{- end -}}
{{- end -}}
