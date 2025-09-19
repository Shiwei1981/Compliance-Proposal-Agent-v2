

#Install-Module -Name AzureAD
#Import-Module AzureAD
   
$tenantId = '16b3c013-d300-468d-ac64-7eda0820b6d3'
$SubscriptionId = '58aa6c07-2c69-4922-9196-19aed3771a8e'
$azureContext = Connect-AzAccount -Tenant $tenantId  
Set-AzContext -SubscriptionId $subscriptionId
Connect-AzureAD

#$OutputCsv = "AdoptedAzureSecurityProducts.csv"
#$AllProviderNamespaces = (Get-AzResourceProvider -ErrorAction Stop).ProviderNamespace
#$SecurityRelatedProviders = $AllProviderNamespaces | Where-Object {
#$_ -match "Security|Policy|Purview|Defender|KeyVault|Sentinel|Insights|Monitor|DataProtection|Authorization|Blueprint|Advisor|Kusto|ResourceGraph|GuestConfiguration|OperationsManagement"
#}
#$AllResources = Get-AzResource -ErrorAction Stop
#$FilteredResources = $AllResources | Where-Object {
#($_.ResourceType.Split('/')[0]) -in $SecurityRelatedProviders
#}
#$FilteredResources |
#Select-Object ResourceName, ResourceType, ResourceGroupName, Location, SubscriptionId |
#Export-Csv -Path $OutputCsv -NoTypeInformation -Encoding UTF8
#Get-AzPolicyDefinition |   
#    Select-Object -Property Name, DisplayName |   
#    Export-Csv -Path "AzurePolicyDefinitions.csv" -NoTypeInformation  
  
$ReportFolder = ".\PIPLReport"  
if (-not (Test-Path $ReportFolder)) {  
    New-Item -ItemType Directory -Path $ReportFolder | Out-Null  
}  

Write-Host "开始收集 Azure 对象信息"  

try {  
    $context = Get-AzContext  
    $accountCsv = "$ReportFolder\CurrentAccount.csv"  
    [PSCustomObject]@{  
        AccountName       = $context.Account.Name  
        TenantId          = $context.Tenant.Id  
        Environment       = $context.Environment.Name  
        SubscriptionId    = $context.Subscription.Id  
        SubscriptionName  = $context.Subscription.Name  
        DateTimeCollected = (Get-Date)  
    } | Export-Csv -Path $accountCsv -NoTypeInformation -Encoding UTF8  
}  
catch {  
    return  
}  

Write-Host "[1] 获取订阅列表"  
$subs = Get-AzSubscription  
$subscriptionCsv = "$ReportFolder\Subscriptions.csv"  
$subs | Select-Object SubscriptionId, SubscriptionName, State, TenantId | Export-Csv -Path $subscriptionCsv -NoTypeInformation -Encoding UTF8  

Write-Host "[2] 获取资源组列表"  
$allRGs = Get-AzResourceGroup  
$rgCsv = "$ReportFolder\ResourceGroups.csv"  
$allRGs | Select-Object ResourceGroupName, Location, ProvisioningState, Tags, ManagedBy | Export-Csv -Path $rgCsv -NoTypeInformation -Encoding UTF8  

Write-Host "[3] 获取资源列表"  
$allResources = Get-AzResource  
$resourcesCsv = "$ReportFolder\Resources.csv"  
$allResources | Select-Object ResourceName, ResourceType, ResourceGroupName, Location, SubscriptionId, Tags | Export-Csv -Path $resourcesCsv -NoTypeInformation -Encoding UTF8  

Write-Host "[4] 获取角色分配列表"  
$roleAssignments = @()
foreach ($sub in $subs) {
Set-AzContext -SubscriptionId $sub.SubscriptionId | Out-Null
$temp = Get-AzRoleAssignment
if ($temp) { $roleAssignments += $temp }
}
$roleAssignCsv = "$ReportFolder\RoleAssignments.csv"
if ($roleAssignments) {
$roleAssignments | Select-Object DisplayName,SignInName,RoleDefinitionName,Scope,PrincipalType | Export-Csv -Path $roleAssignCsv -NoTypeInformation -Encoding UTF8
}







Write-Host "[5] 获取 Key Vault 及 Key/Secret 元数据"  
$keyVaults = Get-AzKeyVault -ErrorAction SilentlyContinue  
if ($keyVaults) {  
    $kvCsv = "$ReportFolder\KeyVaults.csv"  
    $keyVaults | Select-Object VaultName, ResourceId, Location, ResourceGroupName, EnabledForDeployment, EnabledForTemplateDeployment, EnabledForDiskEncryption, TenantId, Tags | Export-Csv -Path $kvCsv -NoTypeInformation -Encoding UTF8  
    $kvKeysCsv = "$ReportFolder\KeyVaultKeys.csv"  
    $kvSecretsCsv = "$ReportFolder\KeyVaultSecrets.csv"  
    $allKVKeys = @()  
    $allKVSecrets = @()  
    foreach ($vault in $keyVaults) {  
        $vaultName = $vault.VaultName  
        $kvKeys = Get-AzKeyVaultKey -VaultName $vaultName -ErrorAction SilentlyContinue  
        if ($kvKeys) {  
            $kvKeys | ForEach-Object {  
                $allKVKeys += [PSCustomObject]@{  
                    VaultName  = $vaultName  
                    KeyName    = $_.Name  
                    KeyVersion = $_.Version  
                    Created    = $_.Created  
                    Updated    = $_.Updated  
                    Enabled    = $_.Enabled  
                    Expires    = $_.Expires  
                    KeyType    = $_.KeyType  
                    KeyOps     = ($_.KeyOps -join ";")  
                }  
            }  
        }  
        $kvSecrets = Get-AzKeyVaultSecret -VaultName $vaultName -ErrorAction SilentlyContinue  
        if ($kvSecrets) {  
            $kvSecrets | ForEach-Object {  
                $allKVSecrets += [PSCustomObject]@{  
                    VaultName     = $vaultName  
                    SecretName    = $_.Name  
                    SecretVersion = $_.Version  
                    ContentType   = $_.ContentType  
                    Enabled       = $_.Enabled  
                    Expires       = $_.Expires  
                    Created       = $_.Created  
                    Updated       = $_.Updated  
                }  
            }  
        }  
    }  
    if ($allKVKeys) {  
        $allKVKeys | Export-Csv -Path $kvKeysCsv -NoTypeInformation -Encoding UTF8  
    }  
    if ($allKVSecrets) {  
        $allKVSecrets | Export-Csv -Path $kvSecretsCsv -NoTypeInformation -Encoding UTF8  
    }  
}  

Write-Host "[6] 获取 Storage Account 列表"  
$storageAccounts = Get-AzStorageAccount -ErrorAction SilentlyContinue  
if ($storageAccounts) {  
    $saBasicCsv = "$ReportFolder\StorageAccounts.csv"  
    $saDetailCsv = "$ReportFolder\StorageAccountDetails.csv"  
    $storageAccounts | Select-Object StorageAccountName, ResourceGroupName, Location, SkuName, Kind, CreationTime, EnableHttpsTrafficOnly, AllowBlobPublicAccess, Tags | Export-Csv -Path $saBasicCsv -NoTypeInformation -Encoding UTF8  
    $saDetails = @()  
    foreach ($sa in $storageAccounts) {  
        $saEnc = $sa.Encryption  
        $saNet = $sa.NetworkRuleSet  
        $saDetails += [PSCustomObject]@{  
            StorageAccountName       = $sa.StorageAccountName  
            ResourceGroupName        = $sa.ResourceGroupName  
            SupportsHttpsTrafficOnly = $sa.EnableHttpsTrafficOnly  
            AllowBlobPublicAccess    = $sa.AllowBlobPublicAccess  
            EncryptionServices       = ($saEnc.Services -join ";")  
            EncryptionKeySource      = $saEnc.KeySource  
            Bypass                   = $saNet.Bypass  
            DefaultAction            = $saNet.DefaultAction  
            IPRules                  = ($saNet.IpRules | ForEach-Object { $_.IPAddressOrRange } -join ";")  
            VirtualNetworkRules      = ($saNet.VirtualNetworkRules | ForEach-Object { $_.Id } -join ";")  
        }  
    }  
    $saDetails | Export-Csv -Path $saDetailCsv -NoTypeInformation -Encoding UTF8  
}  

Write-Host "[7] 获取虚拟机列表"  
$vms = Get-AzVM -ErrorAction SilentlyContinue  
if ($vms) {  
    $vmCsv = "$ReportFolder\AzureVMs.csv"  
    $vms | Select-Object Name, ResourceGroupName, Location, ProvisioningState, HardwareProfile, StorageProfile, OSProfile, Tags | Export-Csv -Path $vmCsv -NoTypeInformation -Encoding UTF8  
}  

Write-Host "[8] 获取 Azure Policy"  
try {  
    $policyAssigns = Get-AzPolicyAssignment -ErrorAction SilentlyContinue  
    if ($policyAssigns) {  
        $paCsv = "$ReportFolder\PolicyAssignments.csv"  
        $policyAssigns | Select-Object PolicyAssignmentName, Scope, DisplayName, PolicyDefinitionId, EnforcementMode | Export-Csv -Path $paCsv -NoTypeInformation -Encoding UTF8  
    }  
    $policyDefinitions = Get-AzPolicyDefinition -Custom -ErrorAction SilentlyContinue  
    if ($policyDefinitions) {  
        $pdCsv = "$ReportFolder\PolicyDefinitions.csv"  
        $policyDefinitions | Select-Object PolicyDefinitionName, DisplayName, Mode, PolicyType, Description, Metadata | Export-Csv -Path $pdCsv -NoTypeInformation -Encoding UTF8  
    }  
    $policyStates = Get-AzPolicyState -Top 100 -ErrorAction SilentlyContinue  
    if ($policyStates) {  
        $psCsv = "$ReportFolder\PolicyStates.csv"  
        $policyStates | Select-Object PolicyAssignmentName, ResourceId, ResourceType, ComplianceState, PolicyDefinitionAction, Timestamp | Export-Csv -Path $psCsv -NoTypeInformation -Encoding UTF8  
    }  
}  
catch {}  

Write-Host "[9] 获取近期活动日志"  
try {  
    $startTime = (Get-Date).AddDays(-14)  
    $activityLogs = Get-AzActivityLog -StartTime $startTime -MaxRecord 2000 -DetailedOutput  
    if ($activityLogs) {  
        $alCsv = "$ReportFolder\ActivityLogs.csv"  
        $activityLogs | Select-Object EventTimestamp, Caller, OperationName, ResourceGroupName, ResourceId, Status, Level, SubStatus | Export-Csv -Path $alCsv -NoTypeInformation -Encoding UTF8  
    }  
}  
catch {}  

Write-Host "[10] 获取资源诊断设置"  
$diagSettingsCsv = "$ReportFolder\DiagnosticSettings.csv"  
$diagSettingsData = @()  
foreach ($res in $allResources) {  
    try {  
        $diagSet = Get-AzDiagnosticSetting -ResourceId $res.ResourceId -ErrorAction SilentlyContinue  
        if ($diagSet) {  
            foreach ($s in $diagSet) {  
                $diagSettingsData += [PSCustomObject]@{  
                    ResourceId               = $res.ResourceId  
                    ResourceName             = $res.Name  
                    DiagSettingName          = $s.Name  
                    LogsEnabled              = ($s.Logs.Enabled -join ";")  
                    MetricsEnabled           = ($s.Metrics.Enabled -join ";")  
                    StorageAccountId         = $s.StorageAccountId  
                    EventHubAuthorizationRuleId = $s.EventHubAuthorizationRuleId  
                    EventHubName             = $s.EventHubName  
                    WorkspaceId              = $s.WorkspaceId  
                }  
            }  
        }  
    }  
    catch {}  
}  
if ($diagSettingsData) {  
    $diagSettingsData | Export-Csv -Path $diagSettingsCsv -NoTypeInformation -Encoding UTF8  
}  

Write-Host "[11] 获取 Azure AD 用户与组信息"  
try {  
    $aadUsers = Get-AzureADUser -All $true -ErrorAction SilentlyContinue  
    if ($aadUsers) {  
        $aadUserCsv = "$ReportFolder\AzureADUsers.csv"  
        $aadUsers | Select-Object ObjectId, UserPrincipalName, DisplayName, GivenName, Surname, AccountEnabled, Mail, JobTitle | Export-Csv -Path $aadUserCsv -NoTypeInformation -Encoding UTF8  
    }  
    $aadGroups = Get-AzureADGroup -All $true -ErrorAction SilentlyContinue  
    if ($aadGroups) {  
        $aadGroupCsv = "$ReportFolder\AzureADGroups.csv"  
        $aadGroups | Select-Object ObjectId, DisplayName, Description, MailEnabled, SecurityEnabled, MailNickname | Export-Csv -Path $aadGroupCsv -NoTypeInformation -Encoding UTF8  
    }  
}  
catch {}  

Write-Host "脚本执行结束。CSV 文件保存在: $ReportFolder"