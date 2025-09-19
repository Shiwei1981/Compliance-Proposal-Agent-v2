$currentTime = Get-Date  
$currentTime

$question = "I am a Azure Cloud Solution Architect in Microsoft's Enterprise Services department, and my client is BMW. 
I am working on enhancement recommendations for BMW's building data platform on Azure, 
primarily to address GDPR compliance requirements.

The intended audience for this proposal is the General Manager of Europe subsidiary of BMW. 
"


$sessionid = "aabbcc"
$encodedQuestion = [System.Web.HttpUtility]::UrlEncode($question)  
$uri = "http://127.0.0.1:8000/answerquestion"  
  
# 创建一个包含问题的哈希表  
$body = @{  
    question = $encodedQuestion  
    sessionid = $sessionid
}  

# 将哈希表转换为 JSON 字符串  
$jsonBody = $body | ConvertTo-Json -Depth 3  # 将哈希表转换为 JSON  

# 使用 POST 方法发送请求  
$response = Invoke-RestMethod -Uri $uri -Method Post -Body $jsonBody -ContentType "application/x-www-form-urlencoded"  
$response  

$uri = "http://127.0.0.1:8000/gettoken"  
$response = Invoke-RestMethod -Uri $uri -Method Post -Body $jsonBody -ContentType "application/x-www-form-urlencoded"  
$response  
$currentTime = Get-Date  
$currentTime