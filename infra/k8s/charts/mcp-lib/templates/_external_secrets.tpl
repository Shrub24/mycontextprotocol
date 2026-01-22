{{- define "mcp-lib.externalSecrets.name" -}}
{{- if .Values.externalSecrets.existingSecretName -}}
{{- .Values.externalSecrets.existingSecretName -}}
{{- else if .Values.externalSecrets.secretName -}}
{{- .Values.externalSecrets.secretName -}}
{{- else -}}
mycontextprotocol-external
{{- end -}}
{{- end -}}

{{- define "mcp-lib.externalSecrets.envFrom" -}}
{{- if (default true .Values.externalSecrets.enabled) -}}
- secretRef:
    name: {{ include "mcp-lib.externalSecrets.name" . }}
{{- end -}}
{{- end -}}

{{- define "mcp-lib.externalSecrets.validate" -}}
{{- if and (default true .Values.externalSecrets.enabled) (not .Values.externalSecrets.existingSecretName) (not .Values.externalSecrets.create) -}}
{{- fail "externalSecrets.existingSecretName or externalSecrets.create must be set when externalSecrets.enabled is true" -}}
{{- end -}}
{{- end -}}

{{- define "mcp-lib.externalSecrets.render" -}}
{{- include "mcp-lib.externalSecrets.validate" . -}}
{{- if and (default true .Values.externalSecrets.enabled) (.Values.externalSecrets.create) (not .Values.externalSecrets.existingSecretName) -}}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "mcp-lib.externalSecrets.name" . }}
  namespace: {{ .Release.Namespace }}
type: Opaque
stringData:
{{- range $key, $val := .Values.externalSecrets.data }}
  {{ $key }}: {{ $val | quote }}
{{- end }}
{{- end -}}
{{- end -}}
