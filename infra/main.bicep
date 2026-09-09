// Single-replica evaluation deployment. Data is ephemeral here; see docs/AZURE.md.
targetScope = 'resourceGroup'
param location string = resourceGroup().location
param appName string = 'atlas-admin'
@description('Publicly pullable image URI, preferably pinned by sha256 digest')
param image string
@secure()
param adminPassword string
@secure()
param policyToken string
param adminEmail string = 'admin@example.test'
param aiProvider string = 'demo'
param azureOpenAIEndpoint string = ''
param azureOpenAIDeployment string = ''
@secure()
param azureOpenAIKey string = ''
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${appName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${appName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'admin-password'
          value: adminPassword
        }
        {
          name: 'policy-token'
          value: policyToken
        }
        {
          name: 'azure-ai-key'
          value: azureOpenAIKey
        }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      volumes: [
        {
          name: 'data'
          storageType: 'EmptyDir'
        }
      ]
      containers: [
        {
          name: 'gateway'
          image: image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          volumeMounts: [
            {
              volumeName: 'data'
              mountPath: '/app/data'
            }
          ]
          env: [
            {
              name: 'ADMIN_EMAIL'
              value: adminEmail
            }
            {
              name: 'ADMIN_PASSWORD'
              secretRef: 'admin-password'
            }
            {
              name: 'POLICY_TOKEN'
              secretRef: 'policy-token'
            }
            {
              name: 'POLICY_ADDRESS'
              value: 'localhost:50051'
            }
            {
              name: 'APP_ORIGIN'
              value: 'https://${appName}.${env.properties.defaultDomain}'
            }
            {
              name: 'COOKIE_SECURE'
              value: 'true'
            }
            {
              name: 'DATABASE_PATH'
              value: '/app/data/atlas.db'
            }
            {
              name: 'SEED_DEMO'
              value: 'true'
            }
            {
              name: 'AI_PROVIDER'
              value: aiProvider
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              value: azureOpenAIDeployment
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-ai-key'
            }
          ]
          probes: [
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/ready'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/health'
                port: 8000
              }
              initialDelaySeconds: 20
              periodSeconds: 20
            }
          ]
        }
        {
          name: 'policy'
          image: image
          command: [
            'python'
            '-m'
            'services.policy.server'
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'POLICY_TOKEN'
              secretRef: 'policy-token'
            }
            {
              name: 'POLICY_BIND'
              value: '127.0.0.1:50051'
            }
          ]
        }
      ]
    }
  }
}
output applicationUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
