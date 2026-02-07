{{/*
Expand the name of the chart.
*/}}
{{- define "ldapguard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ldapguard.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ldapguard.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ldapguard.labels" -}}
helm.sh/chart: {{ include "ldapguard.chart" . }}
{{ include "ldapguard.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ldapguard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ldapguard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "ldapguard.api.labels" -}}
{{ include "ldapguard.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Worker labels
*/}}
{{- define "ldapguard.worker.labels" -}}
{{ include "ldapguard.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Web labels
*/}}
{{- define "ldapguard.web.labels" -}}
{{ include "ldapguard.labels" . }}
app.kubernetes.io/component: web
{{- end }}

{{/*
Postgres labels
*/}}
{{- define "ldapguard.postgres.labels" -}}
{{ include "ldapguard.labels" . }}
app.kubernetes.io/component: postgres
{{- end }}

{{/*
Redis labels
*/}}
{{- define "ldapguard.redis.labels" -}}
{{ include "ldapguard.labels" . }}
app.kubernetes.io/component: redis
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ldapguard.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ldapguard.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "ldapguard.namespace" -}}
{{- .Release.Namespace }}
{{- end }}
